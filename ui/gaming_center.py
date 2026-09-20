from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit

from modules.gaming_center import (
    inventory, xbox_services, open_graphics_settings,
    open_game_mode_settings, open_game_bar_settings,
)


class GamingCenterPanel(QWidget):
    """Read-first gaming diagnostics and supported Windows settings shortcuts."""

    def __init__(self, output, run_job, parent=None):
        super().__init__(parent)
        self.output = output
        self.run_job = run_job
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        title = QLabel("Gaming Center")
        title.setObjectName("section")
        layout.addWidget(title)

        info = QLabel(
            "Gaming diagnostics are hardware-aware and read-first. Windows graphics "
            "settings remain user-controlled; this center does not blindly change HAGS, "
            "fullscreen behavior, MPO, GPU drivers or security services."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        row = QHBoxLayout()
        for text, fn in (
            ("Scan gaming configuration", self.scan),
            ("Xbox services", self.show_xbox),
            ("Windows Graphics settings", self.graphics),
            ("Game Mode settings", self.game_mode),
            ("Game Bar settings", self.game_bar),
        ):
            button = QPushButton(text)
            button.clicked.connect(fn)
            row.addWidget(button)
        layout.addLayout(row)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Gaming diagnostics")
        layout.addWidget(self.details, 1)

    def scan(self):
        self.run_job(inventory, done=self._show, fail=self._error)

    def show_xbox(self):
        self.run_job(xbox_services, done=self._show, fail=self._error)

    def _open_settings(self, fn):
        try:
            self._show(fn())
        except Exception as exc:
            self._error(f"{type(exc).__name__}: {exc}")

    def graphics(self):
        self._open_settings(open_graphics_settings)

    def game_mode(self):
        self._open_settings(open_game_mode_settings)

    def game_bar(self):
        self._open_settings(open_game_bar_settings)

    def _show(self, value):
        self.details.setPlainText(str(value))
        self.output.setPlainText(str(value))

    def _error(self, error):
        self.details.setPlainText(f"Operation failed:\n{error}")
        self.output.setPlainText(f"Operation failed:\n{error}")
