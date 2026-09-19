from PySide6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QMessageBox

from modules import developer_center as dev


class DeveloperCenterPanel(QWidget):
    def __init__(self, output, run_job, is_admin, parent=None):
        super().__init__(parent)
        self.output,self.run_job,self.is_admin=output,run_job,is_admin
        self._build()

    def _build(self):
        layout=QVBoxLayout(self)
        title=QLabel("Developer & Remote Access Center"); title.setObjectName("section"); layout.addWidget(title)
        info=QLabel("Read-first developer workstation diagnostics. Installation and service actions are explicit; SSH and Developer Mode are not enabled automatically.")
        info.setObjectName("muted"); info.setWordWrap(True); layout.addWidget(info)

        row=QHBoxLayout()
        for label,fn in [
            ("Scan environment",self.scan),("Developer settings",self.open_dev),
            ("Optional Features",self.open_features),("Environment variables",self.open_env),
            ("Open Terminal",self.open_terminal)
        ]:
            b=QPushButton(label); b.clicked.connect(fn); row.addWidget(b)
        layout.addLayout(row)

        row2=QHBoxLayout()
        for label,fn in [
            ("WSL status",self.wsl),("Install WSL",self.install_wsl),
            ("OpenSSH status",self.ssh),("Start SSH",self.start_ssh),
            ("Stop SSH",self.stop_ssh)
        ]:
            b=QPushButton(label); b.clicked.connect(fn); row2.addWidget(b)
        layout.addLayout(row2)

        row3=QHBoxLayout()
        for label,fn in [("Enable Developer Mode",lambda:self.set_dev(True)),("Disable Developer Mode",lambda:self.set_dev(False))]:
            b=QPushButton(label); b.clicked.connect(fn); row3.addWidget(b)
        layout.addLayout(row3)

        self.output_area=output
        layout.addWidget(QLabel("Diagnostics and operation output:"))
        layout.addWidget(output,1)

    def _run(self,fn): self.run_job(fn,done=self._show,fail=self._error)
    def scan(self):
        self._run(lambda: __import__("json").dumps(dev.parsed_inventory(),indent=2))
    def wsl(self): self._run(dev.wsl_status)
    def ssh(self): self._run(dev.ssh_status)
    def open_dev(self): self._run(dev.open_developer_settings)
    def open_features(self): self._run(dev.open_optional_features)
    def open_env(self): self._run(dev.open_environment_settings)
    def open_terminal(self): self._run(dev.open_terminal)
    def start_ssh(self):
        if not self.is_admin(): QMessageBox.warning(self,"Administrator required","Starting OpenSSH Server requires Administrator access."); return
        if QMessageBox.question(self,"Start OpenSSH Server","Start the sshd service? This exposes an SSH server according to its Windows configuration.")==QMessageBox.StandardButton.Yes: self._run(dev.start_sshd)
    def stop_ssh(self):
        if not self.is_admin(): QMessageBox.warning(self,"Administrator required","Stopping OpenSSH Server requires Administrator access."); return
        if QMessageBox.question(self,"Stop OpenSSH Server","Stop the sshd service?")==QMessageBox.StandardButton.Yes: self._run(dev.stop_sshd)
    def install_wsl(self):
        if not self.is_admin(): QMessageBox.warning(self,"Administrator required","WSL installation may require Administrator access."); return
        if QMessageBox.question(self,"Install WSL","Run Microsoft's wsl --install --no-launch command? A restart may be required.")==QMessageBox.StandardButton.Yes: self._run(dev.install_wsl)
    def set_dev(self,enabled):
        if not self.is_admin(): QMessageBox.warning(self,"Administrator required","Developer Mode requires Administrator access."); return
        action="enable" if enabled else "disable"
        if QMessageBox.question(self,"Developer Mode",f"Are you sure you want to {action} Developer Mode?") == QMessageBox.StandardButton.Yes: self._run(lambda:dev.set_developer_mode(enabled))
    def _show(self,value): self.output_area.setPlainText(str(value))
    def _error(self,error): self.output_area.setPlainText(f"Operation failed:\n{error}")
