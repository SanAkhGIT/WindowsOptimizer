from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QTextEdit, QCheckBox, QMessageBox
from core.system_info import get_system_info, is_admin
from core.backup import BackupManager
from tweaks.ui_tweaks import scan_ui_tweaks, apply_tweak
from tweaks.personalization import scan_personalization

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Optimizer")
        self.resize(1050, 720)
        self.backup = BackupManager()
        self.tweaks = []
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        title = QLabel("Windows 11 Optimizer")
        title.setStyleSheet("font-size: 24px; font-weight: 700;")
        layout.addWidget(title)
        self.status = QLabel()
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        for label, fn in [("Scan System", self.refresh), ("Create Backup", self.create_backup), ("Apply Selected", self.apply_selected)]:
            b = QPushButton(label)
            b.clicked.connect(fn)
            buttons.addWidget(b)
        layout.addLayout(buttons)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output, 1)
        self.options = QWidget()
        self.options_layout = QVBoxLayout(self.options)
        layout.addWidget(self.options)

    def refresh(self):
        info = get_system_info()
        self.status.setText(f"Windows: {info['windows']} | Build: {info['build']} | CPU: {info['cpu']} | RAM: {info['ram_gb']} GB | Admin: {is_admin()}")
        self.tweaks = scan_ui_tweaks() + scan_personalization()
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.checks = []
        for tweak in self.tweaks:
            cb = QCheckBox(f"{tweak['name']}  [{tweak['risk']}] — {tweak['description']}")
            cb.setChecked(tweak.get("recommended", False))
            cb.setProperty("tweak_id", tweak["id"])
            self.options_layout.addWidget(cb)
            self.checks.append(cb)
        self.output.setPlainText("SCAN COMPLETE\n\n" + "\n".join(f"• {t['name']}: {t['description']}" for t in self.tweaks))

    def create_backup(self):
        try:
            path = self.backup.create()
            QMessageBox.information(self, "Backup created", str(path))
        except Exception as e:
            QMessageBox.critical(self, "Backup failed", str(e))

    def apply_selected(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Restart this application as Administrator before applying system-wide changes.")
            return
        selected = {cb.property("tweak_id") for cb in self.checks if cb.isChecked()}
        if not selected:
            QMessageBox.information(self, "Nothing selected", "Select at least one tweak.")
            return
        self.backup.create()
        results = []
        for tweak in self.tweaks:
            if tweak["id"] in selected:
                try:
                    results.append(f"{tweak['id']}: {apply_tweak(tweak)}")
                except Exception as e:
                    results.append(f"{tweak['id']}: FAILED — {e}")
        self.output.setPlainText("\n".join(results))
        QMessageBox.information(self, "Finished", "Selected operations completed. Review the log/output and restart if requested.")
