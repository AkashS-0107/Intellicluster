"""
Pytest configuration and shared fixtures for unit and service tests.
Uses an isolated in-memory SQLite database with StaticPool for fast, zero-side-effect testing.
"""

from collections.abc import Generator
import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

import intellicluster.models  # noqa: F401
from intellicluster.db.base import Base
from intellicluster.db.session import get_db
from intellicluster.main import app


@pytest.fixture(scope="session")
def test_engine():
    """Create a persistent in-memory SQLite database for test execution."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    # Create tables once for session
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Yields a fresh, transactional database session for each test function.
    Rolls back any uncommitted changes to guarantee test isolation.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection, autocommit=False, autoflush=False)
    session = session_factory()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """
    FastAPI TestClient with overridden get_db and rate_limiter dependencies.
    """
    def override_get_db():
        yield db_session

    from intellicluster.api.deps import rate_limiter

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[rate_limiter] = lambda: None
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
