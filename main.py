import argparse
import faulthandler
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.logging import get_logger, install_exception_hook, setup_logging


def _run_maintenance():
    from modules.maintenance import run_daily_maintenance

    results = run_daily_maintenance()
    for result in results:
        print(f"{result.name}: {result.status} - {result.message}")
    return 0 if all(result.status != "FAILED" for result in results) else 1


def main():
    session_log = setup_logging()
    log_dir = session_log.parent
    crash_path = log_dir / f"{session_log.stem}_crash.log"
    crash_file = None
    try:
        crash_file = crash_path.open("a", encoding="utf-8")
        faulthandler.enable(file=crash_file)
    except OSError:
        crash_file = None

    install_exception_hook()
    logger = get_logger(__name__)
    logger.info(
        "Startup requested | argv=%r | session_log=%s | crash_log=%s",
        sys.argv,
        session_log,
        crash_path if crash_file else "unavailable",
    )

    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--maintenance", choices=["daily"])
    args, _ = parser.parse_known_args()

    if args.maintenance == "daily":
        logger.info("Starting daily maintenance mode")
        try:
            return _run_maintenance()
        finally:
            if crash_file:
                crash_file.flush()
                crash_file.close()

    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Windows Optimizer")
        app.setOrganizationName("WindowsOptimizer")

        from app import MainWindow
        from ui.theme import apply_theme

        apply_theme(app)
        logger.info("QApplication created; starting GUI")
        window = MainWindow()
        window.show()
        logger.info("Main window shown")
        return app.exec()
    except BaseException:
        logger.exception("Fatal GUI startup failure")
        raise
    finally:
        if crash_file:
            crash_file.flush()
            crash_file.close()


if __name__ == "__main__":
    sys.exit(main())
