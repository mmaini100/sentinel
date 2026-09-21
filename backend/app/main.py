"""
Sentinel backend — FastAPI application entry point.

On startup:
1. Run Alembic migrations programmatically
2. Seed services from services.yaml
3. Cache dependency graph in Redis
4. Start Redis Streams consumer as a background task

Exposes a /health endpoint for liveness checks.
"""

import asyncio
import json
import logging
import os
import subprocess
import sys
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import async_session_factory
from app.ingestion.consumer import EventConsumer
from app.ingestion.seeder import (
    cache_dependency_graph,
    load_services_yaml,
    seed_services,
)
from app.ai.worker import RCAWorker


# ---------------------------------------------------------------------------
# Structured JSON logging
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """JSON log formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


def setup_logging() -> None:
    """Configure structured JSON logging for the entire application."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler],
        force=True,
    )
    # Quiet down noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("alembic").setLevel(logging.INFO)


setup_logging()
logger = logging.getLogger("sentinel.main")


# ---------------------------------------------------------------------------
# Startup / shutdown
# ---------------------------------------------------------------------------
consumer = EventConsumer()
consumer_task: asyncio.Task | None = None

rca_worker = RCAWorker()
rca_worker_task: asyncio.Task | None = None



def run_migrations() -> None:
    """Run Alembic migrations via subprocess to avoid async loop conflicts."""
    logger.info("Running Alembic migrations...")
    try:
        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True,
            env=env
        )
        logger.info("Migrations complete")
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e.stderr}")
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown logic."""
    global consumer_task

    # 1. Run migrations
    try:
        run_migrations()
    except Exception:
        logger.exception("Failed to run migrations")
        raise

    # 2. Seed services
    try:
        services_config = load_services_yaml(settings.SERVICES_YAML_PATH)
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)

        async with async_session_factory() as session:
            service_map = await seed_services(session, services_config)
            await cache_dependency_graph(redis_client, service_map, session)

        await redis_client.aclose()
        logger.info("Service seeding and graph caching complete")
    except Exception:
        logger.exception("Failed to seed services")
        raise

    # 3. Start consumer as background task
    consumer_task = asyncio.create_task(consumer.run())
    logger.info("Event consumer started as background task")

    # 4. Start RCA worker as background task
    rca_worker_task = asyncio.create_task(rca_worker.run())
    logger.info("RCA worker started as background task")

    yield

    # Shutdown
    logger.info("Shutting down...")
    
    await rca_worker.stop()
    if rca_worker_task:
        rca_worker_task.cancel()
        try:
            await rca_worker_task
        except asyncio.CancelledError:
            pass

    await consumer.stop()
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass
            
    logger.info("Shutdown complete")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Sentinel",
    description="AI-augmented incident response platform",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
from app.api.auth import router as auth_router
from app.api.services import router as services_router
from app.api.incidents import router as incidents_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(services_router, prefix="/api/v1")
app.include_router(incidents_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Liveness/readiness check — no auth required."""
    return {"status": "ok", "service": "sentinel-backend"}
