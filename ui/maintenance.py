from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.system_info import is_admin
from core.jobs import JobRunner
from core.scheduler import (
    DEFAULT_TIME,
    install_daily_schedule,
    remove_daily_schedule,
    schedule_status,
)
from modules.maintenance import last_runs, run_daily_maintenance


class MaintenancePanel(QWidget):
    def __init__(self, output=None, run_job=None):
        super().__init__()
        self.output = output
        self.run_job = run_job
        self.jobs = JobRunner(self)
        self._refreshing = False
        self._build()
        self.refresh()

    def _build(self):
        layout = QVBoxLayout(self)

        intro = QLabel(
            "<b>Daily Maintenance</b><br>"
            "WindowsOptimizer can run a small, non-interactive maintenance suite "
            "once per day. Cleanup is age-based and skips files that cannot be "
            "safely removed. Memory maintenance is diagnostic only; it does not "
            "periodically purge Windows' file cache."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        schedule_box = QGroupBox("Daily schedule")
        schedule_layout = QVBoxLayout(schedule_box)
        self.status = QLabel()
        self.status.setWordWrap(True)
        schedule_layout.addWidget(self.status)

        buttons = QHBoxLayout()
        self.enable_button = QPushButton(f"Enable Daily Maintenance ({DEFAULT_TIME})")
        self.enable_button.clicked.connect(self.enable)
        buttons.addWidget(self.enable_button)

        self.run_button = QPushButton("Run Now")
        self.run_button.clicked.connect(self.run_now)
        buttons.addWidget(self.run_button)

        self.remove_button = QPushButton("Disable Schedule")
        self.remove_button.clicked.connect(self.disable)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()
        schedule_layout.addLayout(buttons)
        layout.addWidget(schedule_box)

        tasks = QGroupBox("What runs daily")
        tasks_layout = QVBoxLayout(tasks)
        for text in (
            "Remove stale user/system temporary files older than 48 hours",
            "Remove crash/minidump files older than 14 days",
            "Record RAM and pagefile pressure",
            "Check system-drive free space",
            "Inventory mounted volumes",
        ):
            label = QLabel("• " + text)
            label.setWordWrap(True)
            tasks_layout.addWidget(label)
        tasks_layout.addWidget(QLabel(
            "Not included: automatic RAM-cache purging, SFC/DISM, driver "
            "installation, registry sweeping, or automatic software upgrades. "
            "Those remain explicit/manual operations."
        ))
        layout.addWidget(tasks)

        history = QGroupBox("Recent runs")
        history_layout = QVBoxLayout(history)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Time", "Task", "Status", "Details"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        history_layout.addWidget(self.table)
        layout.addWidget(history)

    def refresh(self):
        if self._refreshing:
            return
        self._refreshing = True
        self.status.setText("Checking maintenance schedule…")
        self._refresh_history()
        signals = self.jobs.submit(schedule_status)
        signals.finished.connect(self._apply_schedule_status)
        signals.failed.connect(self._schedule_status_failed)

    def _apply_schedule_status(self, state):
        self._refreshing = False
        if state.get("installed"):
            self.status.setText(
                f"Status: <b>Enabled</b><br>"
                f"State: {state.get('state', 'Unknown')}<br>"
                f"Next run: {state.get('next_run', 'Unknown')}<br>"
                f"Last run: {state.get('last_run', 'Never')}<br>"
                f"Last result: {state.get('last_result', 'Unknown')}"
            )
            self.remove_button.setEnabled(True)
        else:
            error = state.get("error")
            self.status.setText(
                "Status: <b>Not scheduled</b>"
                + (f"<br>Check failed: {error}" if error else "")
            )
            self.remove_button.setEnabled(False)
        # Manual maintenance is useful even when no Task Scheduler entry exists.
        self.run_button.setEnabled(True)

    def _schedule_status_failed(self, error):
        self._refreshing = False
        self.status.setText(f"Unable to read schedule status: {error}")
        self.remove_button.setEnabled(False)
        self.run_button.setEnabled(True)

    def _refresh_history(self):
        runs = last_runs(5)
        rows = []
        for run in runs:
            stamp = run.get("timestamp", "")
            for result in run.get("results", []):
                rows.append(
                    (
                        stamp,
                        result.get("name", ""),
                        result.get("status", ""),
                        result.get("message", ""),
                    )
                )
        self.table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def enable(self):
        if not is_admin():
            QMessageBox.warning(
                self,
                "Administrator required",
                "Run WindowsOptimizer as Administrator to create the system maintenance schedule.",
            )
            return

        def done(message):
            self.refresh()
            if self.output:
                self.output.setPlainText(
                    "DAILY MAINTENANCE ENABLED\n"
                    f"{message}\n\n"
                    "The task runs once per day at 03:00 and can start after a missed run."
                )

        if self.run_job:
            self.run_job(
                install_daily_schedule,
                done=done,
                fail=lambda error: QMessageBox.critical(self, "Schedule failed", str(error)),
                label="Enable daily maintenance schedule",
            )
            return
        try:
            done(install_daily_schedule())
        except Exception as exc:
            QMessageBox.critical(self, "Schedule failed", str(exc))

    def run_now(self):
        def worker():
            return run_daily_maintenance()

        if self.run_job:
            self.run_job(
                worker,
                done=self._run_now_done,
                fail=self._run_now_failed,
                label="Run maintenance now",
            )
            return
        try:
            self._run_now_done(worker())
        except Exception as exc:
            self._run_now_failed(str(exc))

    def _run_now_done(self, results):
        self.refresh()
        summary = "\n".join(
            f"{result.name}: {result.status} — {result.message}"
            for result in results
        )
        if self.output:
            self.output.setPlainText(summary or "Maintenance completed.")

    def _run_now_failed(self, error):
        if self.output:
            self.output.setPlainText(f"Operation failed:\n{error}")
        QMessageBox.critical(self, "Maintenance failed", str(error))

    def disable(self):
        if QMessageBox.question(
            self,
            "Disable daily maintenance",
            "Remove the WindowsOptimizer daily maintenance task?",
        ) != QMessageBox.StandardButton.Yes:
            return

        def done(message):
            self.refresh()
            if self.output:
                self.output.setPlainText(message)

        if self.run_job:
            self.run_job(
                remove_daily_schedule,
                done=done,
                fail=lambda error: QMessageBox.critical(self, "Disable failed", str(error)),
                label="Disable daily maintenance schedule",
            )
            return
        try:
            done(remove_daily_schedule())
        except Exception as exc:
            QMessageBox.critical(self, "Disable failed", str(exc))
