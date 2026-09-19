"""Application-wide diagnostic logging.

Logs are intentionally kept outside the repository and user documents:
%LOCALAPPDATA%\\WindowsOptimizer\\Logs.

A session file captures everything emitted while the application is running.
The rolling application log provides a compact longer-term history.
"""
from __future__ import annotations

import atexit
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import sys
import threading
import traceback
import uuid

APP_NAME = "WindowsOptimizer"
LOG_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / APP_NAME / "Logs"
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 5

_lock = threading.Lock()
_configured = False
_session_path: Path | None = None


def _formatter() -> logging.Formatter:
    return logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_logging() -> Path:
    """Configure process-wide logging once and return the current session path."""
    global _configured, _session_path
    with _lock:
        if _configured and _session_path:
            return _session_path

        LOG_DIR.mkdir(parents=True, exist_ok=True)
        session_id = uuid.uuid4().hex[:12]
        _session_path = LOG_DIR / f"session_{session_id}.log"

        formatter = _formatter()
        root = logging.getLogger()
        root.setLevel(logging.INFO)

        # Avoid duplicate handlers when startup code is imported more than once.
        for handler in list(root.handlers):
            if getattr(handler, "_windows_optimizer_handler", False):
                root.removeHandler(handler)
                handler.close()

        session = RotatingFileHandler(
            _session_path,
            maxBytes=MAX_BYTES,
            backupCount=2,
            encoding="utf-8",
            delay=True,
        )
        session.setFormatter(formatter)
        session._windows_optimizer_handler = True
        root.addHandler(session)

        rolling = RotatingFileHandler(
            LOG_DIR / "application.log",
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
            delay=True,
        )
        rolling.setFormatter(formatter)
        rolling._windows_optimizer_handler = True
        root.addHandler(rolling)

        _configured = True
        logging.getLogger(__name__).info(
            "Application started | pid=%s | session_log=%s",
            os.getpid(),
            _session_path,
        )
        atexit.register(shutdown_logging)
        return _session_path


def get_logger(name: str) -> logging.Logger:
    if not _configured:
        setup_logging()
    return logging.getLogger(name)


def log_exception(logger: logging.Logger, message: str, exc: BaseException) -> None:
    logger.error("%s | %s: %s", message, type(exc).__name__, exc, exc_info=exc)


def install_exception_hook() -> None:
    def handle(exc_type, exc_value, exc_tb):
        logger = get_logger("uncaught")
        logger.error(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_tb),
        )
        sys.__excepthook__(exc_type, exc_value, exc_tb)

    sys.excepthook = handle


def shutdown_logging() -> None:
    global _configured
    if not _configured:
        return
    logging.getLogger(__name__).info("Application shutting down")
    logging.shutdown()
    _configured = False


def current_log_path() -> Path | None:
    return _session_path


def log_directory() -> Path:
    setup_logging()
    return LOG_DIR
