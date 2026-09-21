"""
Redis Streams consumer — reads events from the 'events' stream,
runs anomaly detection, triggers correlation for anomalous events,
and persists everything to PostgreSQL.

Uses a consumer group for reliable delivery with acknowledgment.
Batches inserts for efficiency.
"""

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.correlation.engine import CorrelationEngine
from app.database import async_session_factory
from app.detection.factory import get_detector
from app.detection.interface import AnomalyDetector
from app.models.event import Event
from app.models.service import Service

logger = logging.getLogger("sentinel.consumer")

STREAM_NAME = "events"
GROUP_NAME = "sentinel-consumers"
CONSUMER_NAME = f"consumer-{uuid.uuid4().hex[:8]}"

# Metric names that are numeric and suitable for anomaly detection
DETECTABLE_METRICS = {"request_latency_ms", "error_rate", "cpu_percent", "memory_percent"}
# Log payload fields to check for anomaly signals
LOG_ANOMALY_FIELDS = {"latency_ms": "request_latency_ms", "status_code": None}


class EventConsumer:
    """
    Consumes events from Redis Streams, detects anomalies, correlates
    them into incidents, and persists to PostgreSQL.

    Features:
    - Consumer group for reliable delivery
    - Batch inserts (configurable batch size and flush interval)
    - Automatic reconnection with exponential backoff
    - Service name -> UUID resolution (cached in-memory)
    - Anomaly detection on metric events
    - Correlation of anomalous events into incidents
    """

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None
        self._service_cache: dict[str, uuid.UUID] = {}
        self._service_name_cache: dict[uuid.UUID, str] = {}
        self._batch: list[dict] = []
        self._running = False
        self._detector: AnomalyDetector | None = None
        self._correlation: CorrelationEngine | None = None

    async def _get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection with retry logic."""
        if self._redis is not None:
            try:
                await self._redis.ping()
                return self._redis
            except (aioredis.ConnectionError, aioredis.RedisError):
                self._redis = None

        max_retries = 30
        for attempt in range(max_retries):
            try:
                self._redis = aioredis.from_url(
                    settings.REDIS_URL, decode_responses=True
                )
                await self._redis.ping()
                logger.info(f"Connected to Redis (attempt {attempt + 1})")
                return self._redis
            except (aioredis.ConnectionError, aioredis.RedisError) as e:
                if attempt < max_retries - 1:
                    wait = min(2 ** attempt, 10)
                    logger.warning(
                        f"Redis not ready (attempt {attempt + 1}/{max_retries}), "
                        f"retrying in {wait}s: {e}"
                    )
                    await asyncio.sleep(wait)
                else:
                    raise

    async def _ensure_consumer_group(self) -> None:
        """Create the consumer group if it doesn't exist."""
        r = await self._get_redis()
        try:
            await r.xgroup_create(
                STREAM_NAME, GROUP_NAME, id="0", mkstream=True
            )
            logger.info(
                f"Created consumer group '{GROUP_NAME}' on stream '{STREAM_NAME}'"
            )
        except aioredis.ResponseError as e:
            if "BUSYGROUP" not in str(e):
                raise
            logger.info(f"Consumer group '{GROUP_NAME}' already exists")

    async def _load_service_cache(self) -> None:
        """Load service name -> UUID mapping from the database."""
        async with async_session_factory() as session:
            result = await session.execute(select(Service))
            services = result.scalars().all()
            self._service_cache = {svc.name: svc.id for svc in services}
            self._service_name_cache = {svc.id: svc.name for svc in services}
            logger.info(
                f"Loaded {len(self._service_cache)} services into cache: "
                f"{list(self._service_cache.keys())}"
            )

    def _resolve_service_id(self, service_name: str) -> uuid.UUID | None:
        """Resolve a service name to its UUID."""
        service_id = self._service_cache.get(service_name)
        if service_id is None:
            logger.warning(f"Unknown service: {service_name}")
        return service_id

    def _extract_detectable_value(self, event_data: dict) -> tuple[str, float] | None:
        """
        Extract a (metric_name, value) pair suitable for anomaly detection
        from an event's payload.

        For metric events: use metric_name and value directly.
        For log events: extract latency_ms if present.
        """
        event_type = event_data.get("event_type", "log")
        payload = event_data.get("payload", {})

        if event_type == "metric":
            metric_name = payload.get("metric_name")
            value = payload.get("value")
            if metric_name in DETECTABLE_METRICS and value is not None:
                try:
                    return metric_name, float(value)
                except (TypeError, ValueError):
                    return None

        elif event_type == "log":
            # Check latency from log events
            latency = payload.get("latency_ms")
            if latency is not None:
                try:
                    return "request_latency_ms", float(latency)
                except (TypeError, ValueError):
                    pass

        return None

    def _parse_event(self, raw_data: dict) -> dict | None:
        """Parse a raw Redis Stream message into an event dict."""
        try:
            data_str = raw_data.get("data")
            if not data_str:
                logger.warning(f"Empty event data: {raw_data}")
                return None

            data = json.loads(data_str)
            service_name = data.get("service")
            service_id = self._resolve_service_id(service_name)
            if service_id is None:
                return None

            event_type = data.get("event_type", "log")
            payload = data.get("payload", {})
            timestamp_str = data.get("timestamp")

            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
            else:
                timestamp = datetime.now(timezone.utc)

            # Run anomaly detection
            is_anomalous = False
            anomaly_score = None

            if self._detector:
                detectable = self._extract_detectable_value(data)
                if detectable:
                    metric_name, value = detectable
                    result = self._detector.detect(service_name, metric_name, value)
                    is_anomalous = result.is_anomalous
                    anomaly_score = result.anomaly_score if result.anomaly_score > 0 else None

            return {
                "id": uuid.uuid4(),
                "service_id": service_id,
                "service_name": service_name,  # kept for correlation, not persisted
                "event_type": event_type,
                "payload": payload,
                "is_anomalous": is_anomalous,
                "anomaly_score": anomaly_score,
                "timestamp": timestamp,
            }
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(f"Failed to parse event: {e}, data: {raw_data}")
            return None

    async def _flush_batch(self) -> None:
        """Write the current batch of events to PostgreSQL and correlate anomalies."""
        if not self._batch:
            return

        batch = self._batch.copy()
        self._batch.clear()

        try:
            async with async_session_factory() as session:
                events = []
                anomalous_events = []

                for event_data in batch:
                    service_name = event_data.pop("service_name", None)
                    event = Event(**event_data)
                    events.append(event)
                    session.add(event)

                    if event.is_anomalous and service_name:
                        anomalous_events.append((event, service_name))

                await session.flush()  # Get IDs assigned

                # Correlate anomalous events into incidents
                if self._correlation and anomalous_events:
                    for event, service_name in anomalous_events:
                        await self._correlation.process_anomalous_event(
                            event, service_name, session
                        )

                await session.commit()
                logger.info(
                    f"Flushed {len(events)} events to database "
                    f"({len(anomalous_events)} anomalous)"
                )
        except Exception as e:
            logger.error(f"Failed to flush batch of {len(batch)} events: {e}")
            # Re-add service_name for retry
            self._batch.extend(batch)

    async def run(self) -> None:
        """Main consumer loop — read from Redis Streams and persist to DB."""
        self._running = True
        logger.info("Starting event consumer...")

        await self._ensure_consumer_group()
        await self._load_service_cache()

        # Initialize detector
        try:
            self._detector = get_detector()
            logger.info(f"Anomaly detector initialized: {self._detector.name}")
        except Exception:
            logger.exception("Failed to initialize anomaly detector")
            self._detector = None

        # Initialize correlation engine
        try:
            r = await self._get_redis()
            self._correlation = CorrelationEngine(r)
            logger.info("Correlation engine initialized")
        except Exception:
            logger.exception("Failed to initialize correlation engine")
            self._correlation = None

        last_flush_time = asyncio.get_event_loop().time()
        backoff = 1

        while self._running:
            try:
                r = await self._get_redis()

                # Read new messages
                messages = await r.xreadgroup(
                    groupname=GROUP_NAME,
                    consumername=CONSUMER_NAME,
                    streams={STREAM_NAME: ">"},
                    count=settings.INGESTION_BATCH_SIZE,
                    block=1000,
                )

                for stream, entries in messages:
                    for msg_id, data in entries:
                        event = self._parse_event(data)
                        if event:
                            self._batch.append(event)
                        await r.xack(STREAM_NAME, GROUP_NAME, msg_id)

                # Flush if batch is full or interval elapsed
                current_time = asyncio.get_event_loop().time()
                elapsed = current_time - last_flush_time

                if (
                    len(self._batch) >= settings.INGESTION_BATCH_SIZE
                    or elapsed >= settings.INGESTION_FLUSH_INTERVAL_SECONDS
                ):
                    await self._flush_batch()
                    last_flush_time = current_time

                backoff = 1

            except aioredis.ConnectionError:
                logger.warning(
                    f"Lost Redis connection, retrying in {backoff}s..."
                )
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)
                self._redis = None
            except Exception:
                logger.exception("Unexpected error in consumer loop")
                await asyncio.sleep(backoff)
                backoff = min(backoff * 2, 30)

    async def stop(self) -> None:
        """Gracefully stop the consumer, flushing remaining events."""
        self._running = False
        await self._flush_batch()
        if self._redis:
            await self._redis.aclose()
        logger.info("Event consumer stopped")
