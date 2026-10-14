"""
Unit tests for configuration loading and validation.
"""

from intellicluster.core.config import Settings


def test_default_settings():
    """Verify that default settings instantiate with expected defaults."""
    cfg = Settings()
    assert cfg.APP_NAME == "IntelliCluster Backend"
    assert cfg.APP_ENV in ("development", "test", "production")
    assert cfg.DATABASE_URL.startswith("sqlite")
    assert cfg.NODE_HEARTBEAT_TIMEOUT_SECONDS > 0
    assert cfg.SCHEDULER_STRATEGY == "heuristic"
    assert cfg.LOG_LEVEL in ("DEBUG", "INFO", "WARNING", "ERROR")


def test_custom_settings_override():
    """Verify that configuration attributes can be overridden via constructor."""
    cfg = Settings(
        APP_NAME="CustomCluster",
        APP_ENV="test",
        DEBUG=False,
        DATABASE_URL="sqlite:///./custom.db",
        NODE_HEARTBEAT_TIMEOUT_SECONDS=120,
    )
    assert cfg.APP_NAME == "CustomCluster"
    assert cfg.APP_ENV == "test"
    assert cfg.DEBUG is False
    assert cfg.DATABASE_URL == "sqlite:///./custom.db"
    assert cfg.NODE_HEARTBEAT_TIMEOUT_SECONDS == 120
