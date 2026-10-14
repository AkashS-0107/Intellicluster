"""
Structured application logging configuration.
Supports readable standard logs and structured JSON logging.
"""

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any


class IntelliClusterLogger(logging.Logger):
    """
    Custom Logger that sanitizes extra fields to prevent LogRecord attribute collisions
    (e.g., 'name' conflicting with LogRecord.name in Python 3.13).
    """

    def makeRecord(
        self,
        name: str,
        level: int,
        fn: str,
        lno: int,
        msg: Any,
        args: Any,
        exc_info: Any,
        func: Any = None,
        extra: Any = None,
        sinfo: Any = None,
    ) -> logging.LogRecord:
        if extra and isinstance(extra, dict):
            # Map reserved LogRecord attributes to safe keys to avoid collision in Python 3.13
            safe_extra = {}
            for k, v in extra.items():
                if k == "name":
                    safe_extra["entity_name"] = v
                elif k in ("message", "asctime", "args", "msg", "levelno", "levelname"):
                    safe_extra[f"custom_{k}"] = v
                else:
                    safe_extra[k] = v
            extra = safe_extra
        return super().makeRecord(
            name, level, fn, lno, msg, args, exc_info, func=func, extra=extra, sinfo=sinfo
        )


logging.setLoggerClass(IntelliClusterLogger)


class JSONFormatter(logging.Formatter):
    """Formats log records as structured single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        # Include custom extra attributes if supplied
        extra_fields = getattr(record, "extra_fields", None)
        if isinstance(extra_fields, dict):
            log_data.update(extra_fields)
        return json.dumps(log_data)


def setup_logging(
    level: str = "INFO",
    log_format: str = "text",
) -> logging.Logger:
    """
    Configures and initializes root and application loggers.
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear existing handlers to avoid duplicates
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    if log_format.lower() == "json":
        handler.setFormatter(JSONFormatter())
    else:
        standard_format = (
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s"
        )
        handler.setFormatter(logging.Formatter(standard_format, datefmt="%Y-%m-%d %H:%M:%S"))

    root_logger.addHandler(handler)

    # Silence overly verbose external loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger("intellicluster")
    logger.setLevel(log_level)
    return logger


# Convenience logger instance for intellicluster
logger = logging.getLogger("intellicluster")
