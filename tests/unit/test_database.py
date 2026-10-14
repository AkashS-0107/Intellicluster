"""
Unit tests for database initialization, engine options, and session lifecycle.
"""

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from intellicluster.db.base import Base
from intellicluster.db.session import create_app_engine


def test_tables_created(test_engine):
    """Verify that all four core tables exist in the database."""
    inspector = inspect(test_engine)
    table_names = inspector.get_table_names()

    expected_tables = {"clusters", "nodes", "workloads", "telemetry_snapshots"}
    for table in expected_tables:
        assert table in table_names, f"Table '{table}' missing from database schema."


def test_sqlite_foreign_keys_enabled(db_session: Session):
    """Verify that SQLite foreign key enforcement is active."""
    result = db_session.execute(text("PRAGMA foreign_keys;")).scalar()
    assert result == 1, "Foreign key enforcement is not active in SQLite connection."


def test_custom_sqlite_engine_creation():
    """Verify that custom in-memory SQLite engine creates cleanly."""
    eng = create_app_engine(database_url="sqlite:///:memory:", echo=False)
    assert eng is not None
    with eng.connect() as conn:
        res = conn.execute(text("SELECT 1;")).scalar()
        assert res == 1
