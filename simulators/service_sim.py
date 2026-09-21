"""
Sentinel Microservice Simulator

A parametrized simulator that emits realistic log and metric events to
Redis Streams. Each instance simulates one microservice, configured via
environment variables.

Fault injection modes:
  - latency_spike: Multiply latency by 10-20x
  - error_burst: Spike error rate to 50-80%
  - dependency_timeout: Simulate upstream dependency timeout

Knock-on effects: When a dependency has an active fault, this service
also shows degraded metrics (elevated latency, higher error rate).
"""

import asyncio
import json
import logging
import os
import random
import sys
import time
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis

# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": os.getenv("SERVICE_NAME", "unknown"),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.basicConfig(level=logging.INFO, handlers=[handler])
logger = logging.getLogger("sentinel.simulator")

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------
SERVICE_NAME = os.getenv("SERVICE_NAME", "unknown-service")
SERVICE_DEPS = [
    d.strip() for d in os.getenv("SERVICE_DEPS", "").split(",") if d.strip()
]
BASE_LATENCY_MS = float(os.getenv("BASE_LATENCY_MS", "50"))
BASE_ERROR_RATE = float(os.getenv("BASE_ERROR_RATE", "0.02"))
EMIT_INTERVAL_MIN = float(os.getenv("EMIT_INTERVAL_MIN", "2.0"))
EMIT_INTERVAL_MAX = float(os.getenv("EMIT_INTERVAL_MAX", "5.0"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
FAULT_TTL_SECONDS = int(os.getenv("FAULT_TTL_SECONDS", "120"))

# Redis stream name for events
EVENTS_STREAM = "events"
# Redis key prefix for active faults
FAULT_KEY_PREFIX = "faults:"
# Redis stream for receiving fault commands
FAULT_COMMAND_STREAM = "fault_commands:{service}"

# HTTP status codes weighted by normality
NORMAL_STATUS_CODES = [200, 200, 200, 200, 200, 201, 204, 301, 304]
ERROR_STATUS_CODES = [500, 502, 503, 504, 429]

# Request paths per service type
REQUEST_PATHS = {
    "api-gateway": ["/api/v1/orders", "/api/v1/auth/login", "/api/v1/inventory", "/api/v1/health"],
    "auth-service": ["/auth/login", "/auth/validate", "/auth/refresh", "/auth/logout"],
    "orders-service": ["/orders/create", "/orders/list", "/orders/status", "/orders/cancel"],
    "payments-service": ["/payments/charge", "/payments/refund", "/payments/status", "/payments/webhook"],
    "inventory-service": ["/inventory/check", "/inventory/reserve", "/inventory/release", "/inventory/update"],
}


async def get_redis_client() -> redis.Redis:
    """Create and return a Redis client with retry logic."""
    max_retries = 30
    for attempt in range(max_retries):
        try:
            client = redis.from_url(REDIS_URL, decode_responses=True)
            await client.ping()
            logger.info("Connected to Redis", extra={"attempt": attempt + 1})
            return client
        except (redis.ConnectionError, redis.RedisError) as e:
            if attempt < max_retries - 1:
                wait = min(2 ** attempt, 10)
                logger.warning(
                    f"Redis not ready (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {wait}s: {e}"
                )
                await asyncio.sleep(wait)
            else:
                logger.error("Failed to connect to Redis after all retries")
                raise


async def get_active_fault(r: redis.Redis, service: str) -> dict | None:
    """Check if there's an active fault for a given service."""
    fault_key = f"{FAULT_KEY_PREFIX}{service}"
    fault_data = await r.get(fault_key)
    if fault_data:
        try:
            return json.loads(fault_data)
        except json.JSONDecodeError:
            return None
    return None


async def check_dependency_faults(r: redis.Redis) -> dict:
    """
    Check if any of this service's dependencies have active faults.
    Returns a dict of {dep_name: fault_info} for degraded deps.
    """
    degraded_deps = {}
    for dep in SERVICE_DEPS:
        fault = await get_active_fault(r, dep)
        if fault:
            degraded_deps[dep] = fault
    return degraded_deps


def compute_metrics(
    active_fault: dict | None,
    degraded_deps: dict,
) -> tuple[float, float, float, float, int]:
    """
    Compute current latency, error_rate, cpu, memory, and status_code
    based on active faults (own + dependency knock-on effects).

    Returns: (latency_ms, error_rate, cpu_percent, memory_percent, status_code)
    """
    latency = BASE_LATENCY_MS
    error_rate = BASE_ERROR_RATE
    cpu_percent = random.uniform(15, 35)
    memory_percent = random.uniform(40, 60)

    # Apply own faults
    if active_fault:
        fault_type = active_fault.get("fault_type")
        if fault_type == "latency_spike":
            latency *= random.uniform(10, 20)
            cpu_percent = random.uniform(60, 95)
        elif fault_type == "error_burst":
            error_rate = random.uniform(0.50, 0.80)
            cpu_percent = random.uniform(50, 80)
        elif fault_type == "dependency_timeout":
            latency *= random.uniform(5, 15)
            error_rate = min(error_rate * 5, 0.60)
            cpu_percent = random.uniform(40, 70)

    # Apply knock-on effects from degraded dependencies
    if degraded_deps:
        dep_count = len(degraded_deps)
        for dep_name, dep_fault in degraded_deps.items():
            dep_fault_type = dep_fault.get("fault_type")
            if dep_fault_type == "latency_spike":
                # Downstream latency spike propagates as elevated latency
                latency += BASE_LATENCY_MS * random.uniform(2, 5)
                error_rate = min(error_rate + 0.05 * dep_count, 0.40)
            elif dep_fault_type == "error_burst":
                # Downstream error burst causes some cascading errors
                error_rate = min(error_rate + 0.10 * dep_count, 0.50)
                latency += BASE_LATENCY_MS * random.uniform(0.5, 2)
            elif dep_fault_type == "dependency_timeout":
                # Timeout propagates strongly
                latency += BASE_LATENCY_MS * random.uniform(3, 8)
                error_rate = min(error_rate + 0.15 * dep_count, 0.60)

    # Add realistic jitter
    latency *= random.uniform(0.8, 1.2)
    latency = max(1.0, latency)

    # Determine status code based on effective error rate
    if random.random() < error_rate:
        status_code = random.choice(ERROR_STATUS_CODES)
    else:
        status_code = random.choice(NORMAL_STATUS_CODES)

    return latency, error_rate, cpu_percent, memory_percent, status_code


def generate_log_event(
    latency_ms: float,
    status_code: int,
    error_rate: float,
) -> dict:
    """Generate a structured log event."""
    request_id = str(uuid.uuid4())
    path = random.choice(REQUEST_PATHS.get(SERVICE_NAME, ["/unknown"]))

    level = "info"
    message = f"{SERVICE_NAME} processed request"
    if status_code >= 500:
        level = "error"
        message = f"{SERVICE_NAME} request failed with {status_code}"
    elif status_code >= 400:
        level = "warn"
        message = f"{SERVICE_NAME} client error {status_code}"
    elif latency_ms > BASE_LATENCY_MS * 3:
        level = "warn"
        message = f"{SERVICE_NAME} slow request detected"

    return {
        "event_type": "log",
        "service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "level": level,
            "message": message,
            "request_id": request_id,
            "path": path,
            "method": random.choice(["GET", "POST", "PUT", "DELETE"]),
            "latency_ms": round(latency_ms, 2),
            "status_code": status_code,
        },
    }


def generate_metric_event(
    latency_ms: float,
    error_rate: float,
    cpu_percent: float,
    memory_percent: float,
) -> dict:
    """Generate a structured metric event."""
    # Randomly choose which metric to report this cycle
    metric_name = random.choice([
        "request_latency_ms",
        "error_rate",
        "cpu_percent",
        "memory_percent",
    ])

    value_map = {
        "request_latency_ms": round(latency_ms, 2),
        "error_rate": round(error_rate, 4),
        "cpu_percent": round(cpu_percent, 2),
        "memory_percent": round(memory_percent, 2),
    }

    return {
        "event_type": "metric",
        "service": SERVICE_NAME,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "payload": {
            "metric_name": metric_name,
            "value": value_map[metric_name],
            "unit": {
                "request_latency_ms": "ms",
                "error_rate": "ratio",
                "cpu_percent": "percent",
                "memory_percent": "percent",
            }[metric_name],
            "tags": {
                "service": SERVICE_NAME,
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
        },
    }


async def listen_for_fault_commands(r: redis.Redis) -> None:
    """
    Listen on a Redis Stream for fault injection commands targeting
    this service. When received, set a fault key with TTL.
    """
    stream_name = f"fault_commands:{SERVICE_NAME}"

    # Create the stream and consumer group if they don't exist
    try:
        await r.xgroup_create(stream_name, "sim-group", id="0", mkstream=True)
    except redis.ResponseError as e:
        if "BUSYGROUP" not in str(e):
            raise

    consumer_name = f"sim-{SERVICE_NAME}-{uuid.uuid4().hex[:8]}"
    logger.info(f"Listening for fault commands on stream: {stream_name}")

    while True:
        try:
            messages = await r.xreadgroup(
                groupname="sim-group",
                consumername=consumer_name,
                streams={stream_name: ">"},
                count=1,
                block=1000,
            )

            for stream, entries in messages:
                for msg_id, data in entries:
                    fault_type = data.get("fault_type", "latency_spike")
                    duration = int(data.get("duration_seconds", str(FAULT_TTL_SECONDS)))

                    fault_info = {
                        "fault_type": fault_type,
                        "started_at": datetime.now(timezone.utc).isoformat(),
                        "duration_seconds": duration,
                    }

                    fault_key = f"{FAULT_KEY_PREFIX}{SERVICE_NAME}"
                    await r.set(fault_key, json.dumps(fault_info), ex=duration)
                    logger.info(
                        f"Fault activated: {fault_type} for {duration}s",
                        extra={"fault": fault_info},
                    )

                    await r.xack(stream_name, "sim-group", msg_id)

        except redis.ConnectionError:
            logger.warning("Lost Redis connection in fault listener, reconnecting...")
            await asyncio.sleep(2)
        except Exception:
            logger.exception("Error in fault command listener")
            await asyncio.sleep(1)


async def emit_events(r: redis.Redis) -> None:
    """Main event emission loop."""
    logger.info(
        f"Starting simulator for {SERVICE_NAME} "
        f"(deps={SERVICE_DEPS}, base_latency={BASE_LATENCY_MS}ms, "
        f"base_error_rate={BASE_ERROR_RATE})"
    )

    while True:
        try:
            # Check fault status
            active_fault = await get_active_fault(r, SERVICE_NAME)
            degraded_deps = await check_dependency_faults(r)

            # Compute current metrics
            latency_ms, error_rate, cpu_pct, mem_pct, status_code = compute_metrics(
                active_fault, degraded_deps
            )

            # Generate and emit log event
            log_event = generate_log_event(latency_ms, status_code, error_rate)
            await r.xadd(EVENTS_STREAM, {"data": json.dumps(log_event)})

            # Generate and emit metric event
            metric_event = generate_metric_event(latency_ms, error_rate, cpu_pct, mem_pct)
            await r.xadd(EVENTS_STREAM, {"data": json.dumps(metric_event)})

            if active_fault:
                logger.info(
                    f"Emitting under fault: {active_fault.get('fault_type')} "
                    f"(latency={latency_ms:.0f}ms, error_rate={error_rate:.2f})"
                )

            if degraded_deps:
                logger.info(
                    f"Knock-on from degraded deps: {list(degraded_deps.keys())} "
                    f"(latency={latency_ms:.0f}ms, error_rate={error_rate:.2f})"
                )

            # Jittered sleep
            interval = random.uniform(EMIT_INTERVAL_MIN, EMIT_INTERVAL_MAX)
            await asyncio.sleep(interval)

        except redis.ConnectionError:
            logger.warning("Lost Redis connection, reconnecting...")
            await asyncio.sleep(2)
        except Exception:
            logger.exception("Error in event emission loop")
            await asyncio.sleep(1)


async def main() -> None:
    """Entry point: connect to Redis, run event emitter and fault listener."""
    r = await get_redis_client()

    try:
        await asyncio.gather(
            emit_events(r),
            listen_for_fault_commands(r),
        )
    finally:
        await r.aclose()


if __name__ == "__main__":
    asyncio.run(main())
