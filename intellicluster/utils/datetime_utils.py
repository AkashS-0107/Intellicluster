"""
Timezone-aware UTC datetime utilities.
"""

from datetime import datetime, timezone
from typing import Optional


def utcnow() -> datetime:
    """Return current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


def is_older_than(dt: Optional[datetime], seconds: int) -> bool:
    """
    Check if a given datetime is older than the specified seconds relative to now (UTC).
    Returns True if dt is None or threshold exceeded.
    """
    if dt is None:
        return True
    # Ensure dt is timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age_seconds = (utcnow() - dt).total_seconds()
    return age_seconds > seconds
