from PySide6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget,
)

from modules.storage_center import (
    candidates, cleanup_crash_dumps, cleanup_temp, cleanup_update_downloads,
    empty_recycle_bin, open_cleanup_recommendations, open_storage_settings,
    recycle_bin_status, run_disk_cleanup, system_drive,
)


class StorageCenterPanel(QWidget):
    def __init__(self, output, run_job, is_admin, parent=None):
        super().__init__(parent)
        self.output = output
        self.run_job = run_job
        self.is_admin = is_admin
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 12)
        layout.setSpacing(12)

        title = QLabel("Storage Center")
        title.setObjectName("title")
        layout.addWidget(title)

        info = QLabel(
            "Analyze first. Cleanup actions are explicit and use age-based or Windows-supported "
            "paths. Downloads and arbitrary user data are never silently deleted."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.status = QLabel("Ready. Run Analyze to inspect reclaimable storage.")
        self.status.setObjectName("pageStatus")
        layout.addWidget(self.status)

        analysis = QGroupBox("Analyze & Windows storage tools")
        analysis_layout = QHBoxLayout(analysis)
        self._add_button(analysis_layout, "Analyze", self.analyze, primary=True)
        self._add_button(analysis_layout, "Storage Sense", self.open_storage)
        self._add_button(analysis_layout, "Cleanup recommendations", self.open_recommendations)
        self._add_button(analysis_layout, "Disk Cleanup", self.disk_cleanup)
        self._add_button(analysis_layout, "Recycle Bin status", self.recycle_status)
        layout.addWidget(analysis)

        actions = QGroupBox("Cleanup actions")
        actions_layout = QHBoxLayout(actions)
        self._add_button(actions_layout, "Clean user temp", self.clean_temp)
        self._add_button(actions_layout, "Clean crash dumps", self.clean_crash)
        self._add_button(actions_layout, "Clean Update cache", self.clean_update)
        self._add_button(actions_layout, "Empty Recycle Bin", self.empty_bin)
        layout.addWidget(actions)

        results = QGroupBox("Storage findings")
        results_layout = QVBoxLayout(results)
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Category", "Size", "Risk", "Path", "Description"])
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setAlternatingRowColors(True)
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        for column in range(4):
            header.setSectionResizeMode(column, header.ResizeMode.ResizeToContents)
        results_layout.addWidget(self.table, 1)
        layout.addWidget(results, 1)

    @staticmethod
    def _add_button(layout, label, callback, primary=False):
        button = QPushButton(label)
        if primary:
            button.setObjectName("primary")
        button.clicked.connect(callback)
        layout.addWidget(button)

    def analyze(self):
        self.status.setText("Working: analyzing storage…")
        self.run_job(self._analysis, done=self._show, fail=self._error)

    def _analysis(self):
        drive = system_drive()
        items = candidates()
        lines = [
            f"System drive: {drive['free']/1024**3:.1f} GB free / "
            f"{drive['total']/1024**3:.1f} GB total"
        ]
        for item in items:
            lines.append(
                f"{item.name}: {item.size_bytes/1024**2:.1f} MB | "
                f"{item.risk} | {item.path}"
            )
        return "\n".join(lines), items

    def _show(self, result):
        text, items = result if isinstance(result, tuple) else (str(result), [])
        self.status.setText(
            f"Analysis complete • {len(items)} cleanup candidate(s) found."
        )
        self.output.setPlainText(text)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            values = [
                item.name,
                f"{item.size_bytes/1024**2:.1f} MB",
                item.risk,
                item.path,
                item.description,
            ]
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(str(value)))

    def _confirm(self, title, message):
        return QMessageBox.question(
            self, title, message
        ) == QMessageBox.StandardButton.Yes

    def clean_temp(self):
        if self._confirm(
            "Clean temporary files",
            "Remove user temporary files older than 48 hours? In-use files will be skipped.",
        ):
            self.run_job(cleanup_temp, done=self._show_result, fail=self._error)

    def clean_crash(self):
        if self._confirm(
            "Clean crash dumps",
            "Remove user crash dumps older than 14 days?",
        ):
            self.run_job(cleanup_crash_dumps, done=self._show_result, fail=self._error)

    def clean_update(self):
        if not self.is_admin():
            QMessageBox.warning(
                self,
                "Administrator required",
                "Run as Administrator to clean the Windows Update download cache.",
            )
            return
        if self._confirm(
            "Clean Update cache",
            "Remove files from the Windows Update download cache? Windows can recreate these files.",
        ):
            self.run_job(cleanup_update_downloads, done=self._show_result, fail=self._error)

    def empty_bin(self):
        if self._confirm(
            "Empty Recycle Bin",
            "Permanently remove items currently in the Recycle Bin?",
        ):
            self.run_job(empty_recycle_bin, done=self._show_result, fail=self._error)

    def recycle_status(self):
        self.run_job(recycle_bin_status, done=self._show_result, fail=self._error)

    def _open_settings(self, fn):
        try:
            self._show_result(fn())
        except Exception as exc:
            self._error(f"{type(exc).__name__}: {exc}")

    def open_storage(self):
        self._open_settings(open_storage_settings)

    def open_recommendations(self):
        self._open_settings(open_cleanup_recommendations)

    def disk_cleanup(self):
        self.run_job(run_disk_cleanup, done=self._show_result, fail=self._error)

    def _show_result(self, value):
        self.output.setPlainText(str(value))
        self.status.setText("Operation complete.")

    def _error(self, error):
        self.output.setPlainText(f"Operation failed:\n{error}")
        self.status.setText("Operation failed. See Activity for details.")
