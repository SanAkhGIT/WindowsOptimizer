import sys
import argparse
from core.logging import setup_logging, install_exception_hook, get_logger
from PySide6.QtWidgets import QApplication

from app import MainWindow
from ui.theme import apply_theme


def _run_maintenance():
    from modules.maintenance import run_daily_maintenance

    results = run_daily_maintenance()
    for result in results:
        print(f"{result.name}: {result.status} - {result.message}")
    return 0 if all(result.status != "FAILED" for result in results) else 1


def main():
    session_log = setup_logging()
    install_exception_hook()
    logger = get_logger(__name__)
    logger.info("Startup requested | argv=%r | session_log=%s", sys.argv, session_log)
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--maintenance", choices=["daily"])
    args, _ = parser.parse_known_args()

    if args.maintenance == "daily":
        logger.info("Starting daily maintenance mode")
        return _run_maintenance()

    app = QApplication(sys.argv)
    app.setApplicationName("Windows Optimizer")
    app.setOrganizationName("WindowsOptimizer")
    apply_theme(app)

    logger.info("Starting GUI")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
