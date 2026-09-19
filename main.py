import sys
import argparse
from PySide6.QtWidgets import QApplication
from app import MainWindow


def _run_maintenance():
    from modules.maintenance import run_daily_maintenance

    results = run_daily_maintenance()
    for result in results:
        print(f"{result.name}: {result.status} - {result.message}")
    return 0 if all(result.status != "FAILED" for result in results) else 1


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--maintenance", choices=["daily"])
    args, _ = parser.parse_known_args()

    if args.maintenance == "daily":
        return _run_maintenance()

    app = QApplication(sys.argv)
    app.setApplicationName("Windows Optimizer")
    app.setOrganizationName("WindowsOptimizer")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
