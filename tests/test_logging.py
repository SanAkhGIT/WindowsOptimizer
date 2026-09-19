import logging

import core.logging as app_logging


def test_setup_logging_creates_session_file(tmp_path, monkeypatch):
    app_logging.shutdown_logging()
    monkeypatch.setattr(app_logging, "LOG_DIR", tmp_path)
    app_logging._configured = False
    app_logging._session_path = None

    session = app_logging.setup_logging()
    logger = logging.getLogger("test")
    logger.info("diagnostic test event")
    for handler in logging.getLogger().handlers:
        handler.flush()

    assert session.exists()
    assert "diagnostic test event" in session.read_text(encoding="utf-8")

    app_logging.shutdown_logging()


def test_log_exception_writes_traceback(tmp_path, monkeypatch):
    app_logging.shutdown_logging()
    monkeypatch.setattr(app_logging, "LOG_DIR", tmp_path)
    app_logging._configured = False
    app_logging._session_path = None

    app_logging.setup_logging()
    logger = app_logging.get_logger("test")

    try:
        raise RuntimeError("diagnostic failure")
    except RuntimeError as exc:
        app_logging.log_exception(logger, "Expected test failure", exc)

    for handler in logging.getLogger().handlers:
        handler.flush()

    text = app_logging.current_log_path().read_text(encoding="utf-8")
    assert "Expected test failure" in text
    assert "RuntimeError: diagnostic failure" in text

    app_logging.shutdown_logging()
