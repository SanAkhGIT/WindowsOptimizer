from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QComboBox, QInputDialog, QMessageBox, QTabWidget
)

from modules.startup_manager import records as startup_records, disable_user_run, restore_user_run
from modules.service_manager import inventory as service_inventory, details as service_details, set_start_mode, restore_start_mode
from modules.power_center import current as power_current, plans as power_plans
from modules.dns_center import inventory as dns_inventory
from modules.storage_center import candidates as storage_categories, system_drive as storage_drive
from modules.services import classify as classify_service, recommendation as service_recommendation, attention as service_attention


class WindowsManagementPanel(QWidget):
    """Searchable management center with explicit, reversible controls."""

    def __init__(self, output, run_job, is_admin, parent=None):
        super().__init__(parent)
        self.output = output
        self.run_job = run_job
        self.is_admin = is_admin
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        title = QLabel("Windows management center")
        title.setObjectName("section")
        layout.addWidget(title)
        info = QLabel(
            "Inventory first. Only current-user startup entries and explicitly selected "
            "service startup modes can be changed here. Dependencies are shown before service stops."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._startup_tab(), "Startup")
        self.tabs.addTab(self._services_tab(), "Services")
        self.tabs.addTab(self._power_tab(), "Power")
        self.tabs.addTab(self._dns_tab(), "DNS")
        self.tabs.addTab(self._storage_tab(), "Storage")
        layout.addWidget(self.tabs, 1)

    def _startup_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh startup")
        refresh.clicked.connect(self.refresh_startup)
        row.addWidget(refresh)
        disable = QPushButton("Disable selected")
        disable.clicked.connect(self.disable_selected_startup)
        row.addWidget(disable)
        restore = QPushButton("Restore disabled entry")
        restore.clicked.connect(self.restore_startup)
        row.addWidget(restore)
        row.addStretch()
        layout.addLayout(row)
        self.startup_table = QTableWidget(0, 6)
        self.startup_table.setHorizontalHeaderLabels(["Name","Source","Scope","User","Command","Control"])
        self.startup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.startup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.startup_table)
        return page

    def refresh_startup(self):
        self.run_job(startup_records, done=self._show_startup, fail=self._show_error)

    def _show_startup(self, data):
        rows = data.get("startup", []) if isinstance(data, dict) else []
        self.startup_table.setRowCount(len(rows))
        for i, item in enumerate(rows):
            values = [
                item.get("Name",""), item.get("source",""), item.get("scope",""),
                item.get("User",""), item.get("Command",""),
                "Available" if item.get("manageable") else "Read-only",
            ]
            for j, value in enumerate(values):
                self.startup_table.setItem(i, j, QTableWidgetItem(str(value)))
        self.output.setPlainText(
            f"STARTUP INVENTORY\n{len(rows)} startup entries found. "
            f"{sum(bool(x.get('manageable')) for x in rows)} current-user Run/RunOnce entries are manageable."
        )

    def _selected_startup(self):
        row = self.startup_table.currentRow()
        if row < 0: return None
        return [self.startup_table.item(row, c).text() for c in range(self.startup_table.columnCount())]

    def disable_selected_startup(self):
        selected = self._selected_startup()
        if not selected or selected[5] != "Available":
            QMessageBox.information(self, "Read-only entry", "Select a manageable current-user Run/RunOnce entry.")
            return
        name, source = selected[0], selected[1]
        if not self.is_admin():
            # HKCU changes do not require elevation; this branch intentionally permits them.
            pass
        run_once = source == "Registry RunOnce"
        if QMessageBox.question(self, "Confirm startup change", f"Disable '{name}' from {source}? A backup will be kept.") != QMessageBox.StandardButton.Yes:
            return
        self.run_job(disable_user_run, name, run_once, done=self._after_startup, fail=self._show_error)

    def restore_startup(self):
        name, ok = QInputDialog.getText(self, "Restore startup", "Exact saved startup value name:")
        if not ok or not name.strip(): return
        options = ["Run", "RunOnce"]
        source, ok = QInputDialog.getItem(self, "Startup key", "Key:", options, 0, False)
        if not ok: return
        self.run_job(restore_user_run, name.strip(), source == "RunOnce", done=self._after_startup, fail=self._show_error)

    def _after_startup(self, value):
        self._show_result(value)
        self.refresh_startup()

    def _services_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh services")
        refresh.clicked.connect(self.refresh_services)
        row.addWidget(refresh)
        details = QPushButton("Dependencies / details")
        details.clicked.connect(self.show_service_details)
        row.addWidget(details)
        change = QPushButton("Change startup mode")
        change.clicked.connect(self.change_service_mode)
        row.addWidget(change)
        restore = QPushButton("Restore saved startup mode")
        restore.clicked.connect(self.restore_service_mode)
        row.addWidget(restore)
        row.addStretch()
        layout.addLayout(row)
        self.service_table = QTableWidget(0, 8)
        self.service_table.setHorizontalHeaderLabels(["Name","Display Name","State","Start Mode","Type","Attention","Account","Path"])
        self.service_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.service_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.service_table)
        return page

    def refresh_services(self):
        self.run_job(service_inventory, done=self._show_services, fail=self._show_error)

    def _show_services(self, raw):
        import json
        data = json.loads(raw)
        if isinstance(data, dict): data = [data]
        self.service_table.setRowCount(len(data))
        for i, item in enumerate(data):
            values = [
                item.get("Name",""), item.get("DisplayName",""), item.get("State",""),
                item.get("StartMode",""), classify_service(item),
                service_attention(item), item.get("StartName",""), item.get("PathName","")
            ]
            for j, value in enumerate(values):
                self.service_table.setItem(i, j, QTableWidgetItem(str(value)))
        review = [item for item in data if service_attention(item) in {"Review", "Attention", "Inspect"}]
        self.output.setPlainText(
            f"SERVICE INVENTORY\n{len(data)} services found. No changes were made.\n"
            f"{len(review)} service(s) require review/inspection; nothing was changed automatically."
        )

    def _selected_service_name(self):
        row = self.service_table.currentRow()
        if row < 0 or not self.service_table.item(row, 0): return ""
        return self.service_table.item(row, 0).text()

    def show_service_details(self):
        name = self._selected_service_name()
        if not name:
            QMessageBox.information(self, "Select service", "Select a service first.")
            return
        self.run_job(service_details, name, done=self._show_result, fail=self._show_error)

    def change_service_mode(self):
        if not self.is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator to change services.")
            return
        name = self._selected_service_name()
        if not name:
            QMessageBox.information(self, "Select service", "Select a service first.")
            return
        mode, ok = QInputDialog.getItem(self, "Startup mode", f"{name}:", ["Automatic","Manual","Disabled"], 1, False)
        if not ok: return
        if QMessageBox.question(self, "Confirm service change", f"Set '{name}' to {mode}? Original startup mode will be saved.") != QMessageBox.StandardButton.Yes:
            return
        self.run_job(set_start_mode, name, mode, done=self._after_service, fail=self._show_error)

    def restore_service_mode(self):
        if not self.is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        name = self._selected_service_name()
        if not name:
            QMessageBox.information(self, "Select service", "Select a service first.")
            return
        if QMessageBox.question(self, "Restore service", f"Restore the saved startup mode for '{name}'?") != QMessageBox.StandardButton.Yes:
            return
        self.run_job(restore_start_mode, name, done=self._after_service, fail=self._show_error)

    def _after_service(self, value):
        self._show_result(value)
        self.refresh_services()

    def _power_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        button = QPushButton("Refresh power plans")
        button.clicked.connect(lambda: self.run_job(lambda: power_current() + "\n\n" + power_plans(), done=self._show_result, fail=self._show_error))
        layout.addWidget(button)
        label = QLabel("Power plan selection remains in the existing explicit controls.")
        label.setObjectName("muted")
        layout.addWidget(label)
        layout.addStretch()
        return page

    def _dns_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        button = QPushButton("Refresh DNS inventory")
        button.clicked.connect(lambda: self.run_job(dns_inventory, done=self._show_result, fail=self._show_error))
        layout.addWidget(button)
        layout.addStretch()
        return page

    def _storage_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        button = QPushButton("Analyze storage")
        button.clicked.connect(self.show_storage)
        layout.addWidget(button)
        layout.addStretch()
        return page

    def show_storage(self):
        def report():
            drive = storage_drive()
            items = storage_categories()
            lines = [
                "STORAGE ANALYSIS",
                f"System drive: {drive['free']/1024**3:.1f} GB free / {drive['total']/1024**3:.1f} GB total",
                "",
            ]
            lines.extend(f"{x.name}: {x.size_bytes/1024**3:.2f} GB — {x.path}" for x in items)
            return "\n".join(lines)
        self.run_job(report, done=self._show_result, fail=self._show_error)

    def _show_result(self, value):
        self.output.setPlainText(str(value))

    def _show_error(self, error):
        self.output.setPlainText(f"Operation failed:\n{error}")
