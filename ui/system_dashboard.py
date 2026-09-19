from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QGridLayout,QLabel,QGroupBox,QTextEdit,QPushButton

from modules.hardware_monitor import cpu,gpu,memory,drives,temperatures,fans

class SystemDashboard(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent)
        self.layout=QVBoxLayout(self)
        self.grid=QGridLayout()
        self.layout.addLayout(self.grid)
        self.details=QTextEdit()
        self.details.setReadOnly(True)
        self.layout.addWidget(self.details)
        self.timer=QTimer(self)
        self.timer.timeout.connect(self.refresh_live)
        self.timer.start(1500)
        self.refresh_live()

    def _card(self,title):
        box=QGroupBox(title); label=QLabel("Loading...")
        label.setWordWrap(True)
        l=QVBoxLayout(box); l.addWidget(label)
        self.grid.addWidget(box,self.grid.rowCount()//3,self.grid.count()%3)
        return label

    def refresh_live(self):
        try:
            c=gpu_data=None
            import json
            c=json.loads(cpu()); gpu_data=json.loads(gpu())
            current=c[0] if isinstance(c,list) else c
            g=gpu_data[0] if isinstance(gpu_data,list) and gpu_data else gpu_data
            cards=[
                ("CPU",f"{current.get('Name','Unknown')}\nLoad: {current.get('LoadPercentage','N/A')}%\nFrequency: {current.get('CurrentClockSpeed','N/A')} MHz / {current.get('MaxClockSpeed','N/A')} MHz"),
                ("GPU",f"{g.get('Name','Unknown')}\nDriver: {g.get('DriverVersion','N/A')}"),
            ]
            self.details.setPlainText("\n\n".join(f"{k}\n{v}" for k,v in cards))
        except Exception as exc:
            self.details.setPlainText(f"Live hardware telemetry unavailable: {exc}\n\nSome firmware exposes temperatures/fans only through vendor/third-party sensors.")
