from PySide6.QtWidgets import (
    QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)

from modules import developer_center as dev


class DeveloperCenterPanel(QWidget):
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

        title = QLabel("Developer & Remote Access")
        title.setObjectName("title")
        layout.addWidget(title)

        info = QLabel(
            "Read-first developer workstation diagnostics. Actions that install components, "
            "change services, or alter Developer Mode require explicit confirmation."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        self.status = QLabel("Ready for a diagnostic scan.")
        self.status.setObjectName("pageStatus")
        layout.addWidget(self.status)

        grid = QGridLayout()
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(12)

        diagnostics = QGroupBox("Diagnostics")
        diagnostics_layout = QGridLayout(diagnostics)
        self._add_button(diagnostics_layout, 0, 0, "Scan environment", self.scan)
        self._add_button(diagnostics_layout, 0, 1, "Developer settings", self.open_dev)
        self._add_button(diagnostics_layout, 1, 0, "Optional Features", self.open_features)
        self._add_button(diagnostics_layout, 1, 1, "Environment variables", self.open_env)
        self._add_button(diagnostics_layout, 2, 0, "Open Terminal", self.open_terminal)
        diagnostics_layout.setColumnStretch(0, 1)
        diagnostics_layout.setColumnStretch(1, 1)
        grid.addWidget(diagnostics, 0, 0)

        remote = QGroupBox("WSL & OpenSSH")
        remote_layout = QGridLayout(remote)
        self._add_button(remote_layout, 0, 0, "WSL status", self.wsl)
        self._add_button(remote_layout, 0, 1, "Install WSL", self.install_wsl)
        self._add_button(remote_layout, 1, 0, "OpenSSH status", self.ssh)
        self._add_button(remote_layout, 1, 1, "Start SSH", self.start_ssh)
        self._add_button(remote_layout, 2, 0, "Stop SSH", self.stop_ssh)
        remote_layout.setColumnStretch(0, 1)
        remote_layout.setColumnStretch(1, 1)
        grid.addWidget(remote, 0, 1)

        developer = QGroupBox("Developer Mode")
        developer_layout = QHBoxLayout(developer)
        enable = QPushButton("Enable Developer Mode")
        enable.clicked.connect(lambda: self.set_dev(True))
        developer_layout.addWidget(enable)
        disable = QPushButton("Disable Developer Mode")
        disable.clicked.connect(lambda: self.set_dev(False))
        developer_layout.addWidget(disable)
        grid.addWidget(developer, 1, 0, 1, 2)

        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        layout.addLayout(grid)
        layout.addStretch(1)

    @staticmethod
    def _add_button(layout, row, column, label, callback):
        button = QPushButton(label)
        button.clicked.connect(callback)
        layout.addWidget(button, row, column)

    def _run(self, fn, label):
        self.status.setText(f"Working: {label}…")
        self.run_job(
            fn,
            done=lambda value: self._show(label, value),
            fail=lambda error: self._error(label, error),
        )

    def scan(self):
        self._run(
            lambda: __import__("json").dumps(dev.parsed_inventory(), indent=2),
            "environment scan",
        )

    def wsl(self):
        self._run(dev.wsl_status, "WSL status")

    def ssh(self):
        self._run(dev.ssh_status, "OpenSSH status")

    def open_dev(self):
        self._run(dev.open_developer_settings, "Developer settings")

    def open_features(self):
        self._run(dev.open_optional_features, "Optional Features")

    def open_env(self):
        self._run(dev.open_environment_settings, "Environment variables")

    def open_terminal(self):
        self._run(dev.open_terminal, "Terminal")

    def start_ssh(self):
        if not self.is_admin():
            QMessageBox.warning(self, "Administrator required", "Starting OpenSSH Server requires Administrator access.")
            return
        if QMessageBox.question(
            self,
            "Start OpenSSH Server",
            "Start the sshd service? This exposes an SSH server according to its Windows configuration.",
        ) == QMessageBox.StandardButton.Yes:
            self._run(dev.start_sshd, "start OpenSSH")

    def stop_ssh(self):
        if not self.is_admin():
            QMessageBox.warning(self, "Administrator required", "Stopping OpenSSH Server requires Administrator access.")
            return
        if QMessageBox.question(
            self,
            "Stop OpenSSH Server",
            "Stop the sshd service?",
        ) == QMessageBox.StandardButton.Yes:
            self._run(dev.stop_sshd, "stop OpenSSH")

    def install_wsl(self):
        if not self.is_admin():
            QMessageBox.warning(self, "Administrator required", "WSL installation may require Administrator access.")
            return
        if QMessageBox.question(
            self,
            "Install WSL",
            "Run Microsoft's wsl --install --no-launch command? A restart may be required.",
        ) == QMessageBox.StandardButton.Yes:
            self._run(dev.install_wsl, "install WSL")

    def set_dev(self, enabled):
        if not self.is_admin():
            QMessageBox.warning(self, "Administrator required", "Developer Mode requires Administrator access.")
            return
        action = "enable" if enabled else "disable"
        if QMessageBox.question(
            self,
            "Developer Mode",
            f"Are you sure you want to {action} Developer Mode?",
        ) == QMessageBox.StandardButton.Yes:
            self._run(lambda: dev.set_developer_mode(enabled), f"{action} Developer Mode")

    def _show(self, label, value):
        self.status.setText(f"Complete: {label}.")
        self.output.setPlainText(str(value))

    def _error(self, label, error):
        self.status.setText(f"Error: {label}.")
        self.output.setPlainText(f"Operation failed:\n{error}")
