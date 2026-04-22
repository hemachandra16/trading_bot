"""
Logging configuration for the trading bot.

Provides dual-output logging:
  - Console: INFO level with rich color formatting via RichHandler.
  - File:    Configurable level (default DEBUG) written to logs/trading_bot.log
             with automatic rotation at 5 MB, keeping 3 backup files.

Usage:
    from bot.logging_config import get_logger
    logger = get_logger(__name__)

Environment:
    LOG_LEVEL — Override file log level (default: DEBUG).
                Example: LOG_LEVEL=INFO uvicorn server:app
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.logging import RichHandler

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_LOG_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "trading_bot.log"
_FILE_FORMAT = "[%(asctime)s] [%(levelname)s] [%(name)s] — %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Ensure the logs directory exists at import time.
_LOG_DIR.mkdir(parents=True, exist_ok=True)

# Allow log level override via environment variable.
# Usage: LOG_LEVEL=INFO uvicorn server:app --reload
_env_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
_file_log_level = getattr(logging, _env_level, logging.DEBUG)

# ---------------------------------------------------------------------------
# Shared handlers (created once, reused across all loggers)
# ---------------------------------------------------------------------------

# Rotate at 5 MB, keep 3 backup files — prevents unbounded growth.
_file_handler = RotatingFileHandler(
    _LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
)
_file_handler.setLevel(_file_log_level)
_file_handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))

_console_handler = RichHandler(
    level=logging.INFO,
    show_time=True,
    show_path=False,
    rich_tracebacks=True,
    markup=True,
)
_console_handler.setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with console and file handlers.

    If the logger already has handlers (i.e. it was previously configured),
    the existing logger is returned as-is to avoid duplicate output.

    Args:
        name: Logical name for the logger, typically ``__name__``.

    Returns:
        A ``logging.Logger`` instance ready for use.
    """
    logger = logging.getLogger(name)

    # Prevent adding duplicate handlers on repeated calls.
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(_file_handler)
        logger.addHandler(_console_handler)
        logger.propagate = False  # prevent messages reaching the root logger

    return logger
