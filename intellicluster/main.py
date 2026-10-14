"""
FastAPI application entry point for IntelliCluster.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from intellicluster import __version__
from intellicluster.api.exception_handlers import register_exception_handlers
from intellicluster.api.v1.router import api_v1_router
from intellicluster.core.config import settings
from intellicluster.core.logging import logger, setup_logging
from intellicluster.db.session import engine, init_db
from intellicluster.utils.datetime_utils import utcnow


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Handles startup table creation, logging init, and graceful shutdown.
    """
    setup_logging(level=settings.LOG_LEVEL, log_format=settings.LOG_FORMAT)
    logger.info(
        "Starting %s (v%s) in '%s' environment",
        settings.APP_NAME,
        __version__,
        settings.APP_ENV,
    )

    # Initialize SQLite database tables
    try:
        init_db(engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.error("Failed to initialize database schema: %s", str(e), exc_info=True)
        raise

    yield

    logger.info("Shutting down %s...", settings.APP_NAME)
    try:
        from intellicluster.services.telemetry_simulator_service import TelemetrySimulatorService
        await TelemetrySimulatorService.get_instance().stop()
    except Exception as e:
        logger.debug("Simulator shutdown error: %s", e)


app = FastAPI(
    title=settings.APP_NAME,
    version=__version__,
    description=(
        "IntelliCluster: ML-Driven Cloud Server Clustering and Workload Orchestration."
    ),
    lifespan=lifespan,
)

# Configure CORS middleware for production and local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register domain exception handlers
register_exception_handlers(app)

# Mount API v1 router
app.include_router(api_v1_router)


@app.get("/", tags=["Root"])
def read_root() -> dict[str, Any]:
    """Basic root welcome message."""
    return {
        "message": "Welcome to IntelliCluster Backend Foundation",
        "version": __version__,
        "step": "Step 1 of 10: Backend Foundation",
        "docs_url": "/docs",
        "health_url": "/health",
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, Any]:
    """
    Health check probe to verify backend and database connectivity.
    """
    db_status = "healthy"
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error("Database health check probe failed: %s", str(e))

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "version": __version__,
        "database": db_status,
        "timestamp": utcnow().isoformat(),
        "step": "1 (Backend)",
    }
