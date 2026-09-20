from datetime import datetime
from PySide6.QtCore import QElapsedTimer, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPlainTextEdit, QProgressBar, QPushButton,
    QVBoxLayout, QWidget,
)


class ActivityPanel(QFrame):
    """Compact global operation state and on-demand diagnostic activity log."""

    errorRaised = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("activityPanel")
        self._timer = QElapsedTimer()
        self._operation_id = None
        self._started_at = None

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 8, 14, 8)
        root.setSpacing(6)

        status_row = QHBoxLayout()
        self.state = QLabel("● Ready")
        self.state.setObjectName("activityState")
        status_row.addWidget(self.state)

        self.operation = QLabel("No active operation")
        self.operation.setObjectName("activityOperation")
        status_row.addWidget(self.operation, 1)

        self.elapsed = QLabel("")
        self.elapsed.setObjectName("activityElapsed")
        status_row.addWidget(self.elapsed)

        self.progress = QProgressBar()
        self.progress.setObjectName("activityProgress")
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setMinimumWidth(140)
        status_row.addWidget(self.progress)

        self.clear = QPushButton("Clear")
        self.clear.setToolTip("Clear diagnostic activity log")
        self.clear.clicked.connect(self.clear_log)
        status_row.addWidget(self.clear)

        self.toggle = QPushButton("Activity")
        self.toggle.setCheckable(True)
        self.toggle.setObjectName("activityToggle")
        self.toggle.clicked.connect(self._toggle_log)
        status_row.addWidget(self.toggle)
        root.addLayout(status_row)

        self.summary = QLabel("")
        self.summary.setObjectName("activitySummary")
        self.summary.setWordWrap(True)
        self.summary.hide()
        root.addWidget(self.summary)

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setObjectName("activityLog")
        self.editor.setMaximumHeight(130)
        self.editor.hide()
        root.addWidget(self.editor)

        self.timer = QTimer(self)
        self.timer.setInterval(250)
        self.timer.timeout.connect(self._update_elapsed)

        self.set_ready()

    def _toggle_log(self, checked):
        self.editor.setVisible(checked)
        self.toggle.setText("Hide activity" if checked else "Activity")

    def _update_elapsed(self):
        if not self._timer.isValid():
            return
        seconds = self._timer.elapsed() / 1000
        self.elapsed.setText(self._format_elapsed(seconds))

    @staticmethod
    def _format_elapsed(seconds):
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes:02d}:{seconds:02d}"

    def append(self, text):
        if text:
            stamp = datetime.now().strftime("%H:%M:%S")
            self.editor.appendPlainText(f"[{stamp}] {text}")
            scrollbar = self.editor.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def set_ready(self):
        self.timer.stop()
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.state.setText("● Ready")
        self.state.setProperty("state", "ready")
        self.operation.setText("Ready")
        self.elapsed.clear()
        self.summary.hide()
        self._repolish()

    def start(self, title, operation_id=None):
        self._operation_id = operation_id
        self._started_at = datetime.now()
        self._timer.start()
        self.timer.start()
        self.progress.setRange(0, 0)
        self.state.setText("● Working")
        self.state.setProperty("state", "working")
        self.operation.setText(title)
        self.elapsed.setText("00:00")
        self.summary.hide()
        self._repolish()

    def success(self, title, summary=""):
        self.timer.stop()
        elapsed = self._timer.elapsed() / 1000 if self._timer.isValid() else 0
        self.progress.setRange(0, 1)
        self.progress.setValue(1)
        self.state.setText("● Complete")
        self.state.setProperty("state", "success")
        self.operation.setText(title)
        self.elapsed.setText(self._format_elapsed(elapsed))
        self._operation_id = None
        self.summary.setText(summary)
        self.summary.setVisible(bool(summary))
        self._repolish()

    def error(self, title, message):
        self.timer.stop()
        elapsed = self._timer.elapsed() / 1000 if self._timer.isValid() else 0
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.state.setText("● Error")
        self.state.setProperty("state", "error")
        self.operation.setText(title)
        self.elapsed.setText(self._format_elapsed(elapsed))
        self._operation_id = None
        self.summary.setText(str(message))
        self.summary.show()
        self.toggle.setChecked(True)
        self._toggle_log(True)
        self._repolish()
        self.errorRaised.emit(str(message))

    def clear_log(self):
        self.editor.clear()
        self.summary.clear()
        self.summary.hide()

    def _repolish(self):
        self.state.style().unpolish(self.state)
        self.state.style().polish(self.state)
