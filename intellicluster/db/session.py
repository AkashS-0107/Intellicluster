"""
Database engine, session management, and connection lifecycle.
Configured with SQLite foreign-key enforcement, WAL mode, and safe session handling.
"""

from typing import Any
from collections.abc import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from intellicluster.core.config import settings
from intellicluster.core.logging import logger
from intellicluster.db.base import Base


def _configure_sqlite_connection(dbapi_connection: Any, connection_record: Any) -> None:
    """Enforce foreign keys and enable WAL mode on SQLite connections."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON;")
    # WAL mode is not supported on purely in-memory databases (:memory:)
    if not str(dbapi_connection).startswith("<sqlite3.Connection object at") or "memory" not in settings.DATABASE_URL:
        try:
            cursor.execute("PRAGMA journal_mode=WAL;")
        except Exception:
            pass
    cursor.close()


def create_app_engine(database_url: str = settings.DATABASE_URL, echo: bool = settings.DB_ECHO) -> Engine:
    """Creates an engine configured with appropriate connection options."""
    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    engine = create_engine(
        database_url,
        echo=echo,
        connect_args=connect_args,
        pool_pre_ping=True,
    )

    if database_url.startswith("sqlite"):
        event.listen(engine, "connect", _configure_sqlite_connection)

    return engine


# Primary engine and session factory
engine = create_app_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency provider yielding a scoped database session.
    Guarantees session closure on completion or exception.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(target_engine: Engine = engine) -> None:
    """
    Initialize database schema by creating all registered tables.
    Safe to call repeatedly (idempotent).
    """
    # Import all models to ensure they are registered with Base.metadata
    import intellicluster.models  # noqa: F401

    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=target_engine)

    # Safely check and add new columns for existing SQLite tables if missing
    try:
        from sqlalchemy import inspect, text
        inspector = inspect(target_engine)
        if "telemetry_snapshots" in inspector.get_table_names():
            columns = {col["name"] for col in inspector.get_columns("telemetry_snapshots")}
            with target_engine.connect() as conn:
                if "workload" not in columns:
                    conn.execute(text("ALTER TABLE telemetry_snapshots ADD COLUMN workload FLOAT"))
                if "resource_allocation" not in columns:
                    conn.execute(text("ALTER TABLE telemetry_snapshots ADD COLUMN resource_allocation FLOAT"))
                conn.commit()
    except Exception as e:
        logger.debug("Schema migration check completed: %s", e)

    logger.info("Database schema initialized successfully.")
