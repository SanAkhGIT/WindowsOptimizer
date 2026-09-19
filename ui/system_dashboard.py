import json

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QVBoxLayout, QWidget,
)

from core.jobs import JobRunner
from modules.hardware_monitor import live, sensors
from modules.system_snapshot import snapshot


class MetricCard(QFrame):
    def __init__(self, title, value="—", hint="", parent=None):
        super().__init__(parent)
        self.setObjectName("metric")
        layout = QVBoxLayout(self)
        title_label = QLabel(title.upper())
        title_label.setObjectName("muted")
        value_label = QLabel(value)
        value_label.setObjectName("metricValue")
        hint_label = QLabel(hint)
        hint_label.setObjectName("metricAccent")
        hint_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        layout.addWidget(hint_label)
        self.value_label = value_label
        self.hint_label = hint_label

    def set_value(self, value, hint=None):
        self.value_label.setText(str(value))
        if hint is not None:
            self.hint_label.setText(str(hint))


class SystemDashboard(QWidget):
    """Modern system cockpit: fast telemetry + slower hardware inventory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.jobs = JobRunner(self)
        self._live_busy = False
        self._inventory_busy = False
        self._sensor_busy = False
        self._hardware_identity = ""
        self._build()
        self._refresh_live()
        self._refresh_inventory()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_live)
        self.timer.start(2000)

        self.sensor_timer = QTimer(self)
        self.sensor_timer.timeout.connect(self._refresh_sensors)
        self.sensor_timer.start(10000)
        QTimer.singleShot(750, self._refresh_sensors)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(22, 20, 22, 20)
        root.setSpacing(14)

        header = QHBoxLayout()
        title = QLabel("System overview")
        title.setObjectName("title")
        header.addWidget(title)
        header.addStretch()
        self.refresh_button = QPushButton("↻ Refresh details")
        self.refresh_button.setObjectName("primary")
        self.refresh_button.clicked.connect(self._refresh_inventory)
        header.addWidget(self.refresh_button)
        root.addLayout(header)

        self.subtitle = QLabel("Live telemetry updates every 2 seconds. Static inventory refreshes separately so the UI stays responsive.")
        self.subtitle.setObjectName("muted")
        root.addWidget(self.subtitle)

        metrics = QGridLayout()
        metrics.setSpacing(12)
        self.cpu_card = MetricCard("CPU load", "—", "waiting for telemetry")
        self.gpu_card = MetricCard("GPU", "—", "waiting for telemetry")
        self.ram_card = MetricCard("Memory", "—", "waiting for telemetry")
        self.disk_card = MetricCard("System drive", "—", "waiting for telemetry")
        for index, card in enumerate((self.cpu_card, self.gpu_card, self.ram_card, self.disk_card)):
            metrics.addWidget(card, 0, index)
        root.addLayout(metrics)

        details = QHBoxLayout()
        details.setSpacing(12)

        identity = QFrame()
        identity.setObjectName("card")
        il = QVBoxLayout(identity)
        heading = QLabel("Machine identity")
        heading.setObjectName("section")
        il.addWidget(heading)
        self.identity = QLabel("Loading…")
        self.identity.setWordWrap(True)
        il.addWidget(self.identity)
        details.addWidget(identity, 1)

        network = QFrame()
        network.setObjectName("card")
        nl = QVBoxLayout(network)
        heading = QLabel("Network")
        heading.setObjectName("section")
        nl.addWidget(heading)
        self.network = QLabel("Loading…")
        self.network.setWordWrap(True)
        nl.addWidget(self.network)
        details.addWidget(network, 1)
        root.addLayout(details)

        lower = QHBoxLayout()
        lower.setSpacing(12)
        hardware = QFrame()
        hardware.setObjectName("card")
        hl = QVBoxLayout(hardware)
        heading = QLabel("Hardware & sensors")
        heading.setObjectName("section")
        hl.addWidget(heading)
        self.hardware = QLabel("Loading…")
        self.hardware.setWordWrap(True)
        hl.addWidget(self.hardware)
        lower.addWidget(hardware, 1)

        drivers = QFrame()
        drivers.setObjectName("card")
        dl = QVBoxLayout(drivers)
        heading = QLabel("Driver inventory")
        heading.setObjectName("section")
        dl.addWidget(heading)
        self.drivers = QLabel("Loading…")
        self.drivers.setWordWrap(True)
        dl.addWidget(self.drivers)
        lower.addWidget(drivers, 1)
        root.addLayout(lower)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setMaximumHeight(145)
        self.details.setPlaceholderText("Detailed system inventory appears here after refresh.")
        root.addWidget(self.details)

    @staticmethod
    def _first(value):
        if isinstance(value, list):
            return value[0] if value else {}
        return value if isinstance(value, dict) else {}

    @staticmethod
    def _gb(value):
        try:
            return f"{float(value) / 1024**3:.1f} GB"
        except (TypeError, ValueError):
            return "—"

    def _refresh_live(self):
        if self._live_busy:
            return
        self._live_busy = True
        signals = self.jobs.submit(live)
        signals.finished.connect(self._live_done)
        signals.failed.connect(self._live_failed)

    def _live_done(self, data):
        self._live_busy = False
        cpu = self._first(data.get("cpu"))
        gpu = self._first(data.get("gpu"))
        memory = self._first(data.get("memory"))
        disk = self._first(data.get("disk"))

        self.cpu_card.set_value(
            f"{cpu.get('LoadPercentage', '—')}%",
            f"{cpu.get('CurrentClockSpeed', '—')} MHz • {cpu.get('Name', 'CPU')}",
        )
        self.gpu_card.set_value(gpu.get("Name", "—"), f"Driver {gpu.get('DriverVersion', '—')}")

        total_kb = float(memory.get("TotalVisibleMemorySize") or 0)
        free_kb = float(memory.get("FreePhysicalMemory") or 0)
        used = ((total_kb - free_kb) / total_kb * 100) if total_kb else 0
        self.ram_card.set_value(f"{used:.0f}%", f"{self._gb((total_kb - free_kb) * 1024)} used")

        free = self._gb(disk.get("FreeSpace"))
        size = self._gb(disk.get("Size"))
        self.disk_card.set_value(free, f"{size} total")

    def _live_failed(self, error):
        self._live_busy = False
        self.subtitle.setText(f"Live telemetry unavailable: {error}")

    def _refresh_sensors(self):
        if self._sensor_busy:
            return
        self._sensor_busy = True
        signals = self.jobs.submit(sensors)
        signals.finished.connect(self._sensors_done)
        signals.failed.connect(self._sensors_failed)

    def _sensors_done(self, data):
        self._sensor_busy = False
        temp = data.get("temperatures", [])
        fan = data.get("fans", [])
        temp_items = temp if isinstance(temp, list) else [temp]
        fan_items = fan if isinstance(fan, list) else [fan]

        celsius = []
        for item in temp_items:
            try:
                celsius.append((float(item.get("CurrentTemperature")) / 10) - 273.15)
            except (TypeError, ValueError):
                continue

        if celsius:
            sensor_text = f"Average thermal-zone temperature: {sum(celsius) / len(celsius):.1f} °C"
        else:
            sensor_text = "Temperature: not exposed by Windows firmware"
        fan_count = sum(1 for item in fan_items if isinstance(item, dict) and item.get("Name"))
        sensor_text += f"<br>Fans detected: {fan_count}" if fan_count else "<br>Fans detected: not exposed by Windows firmware"

        prefix = f"{self._hardware_identity}<br>" if self._hardware_identity else ""
        self.hardware.setText(prefix + sensor_text)

    def _sensors_failed(self, _error):
        self._sensor_busy = False

    def _refresh_inventory(self):
        if self._inventory_busy:
            return
        self._inventory_busy = True
        self.refresh_button.setEnabled(False)
        signals = self.jobs.submit(snapshot)
        signals.finished.connect(self._inventory_done)
        signals.failed.connect(self._inventory_failed)

    def _inventory_done(self, data):
        self._inventory_busy = False
        self.refresh_button.setEnabled(True)
        info = data.get("system", {})
        self.identity.setText(
            f"<b>{data.get('hostname', 'Unknown')}</b><br>"
            f"{info.get('windows', 'Windows')}<br>"
            f"Build {info.get('build', '—')} • {info.get('device_type', '—')} • "
            f"{info.get('ram_gb', '—')} GB RAM<br>"
            f"CPU: {info.get('cpu', '—')}<br>GPU: {info.get('gpu', '—')}"
        )

        adapters = data.get("network", [])
        if adapters:
            rows = []
            for item in adapters[:4]:
                rows.append(
                    f"{item.get('InterfaceAlias', 'Adapter')}: "
                    f"{item.get('IPv4Address') or 'No IPv4'} • DNS {item.get('DNSServer') or '—'}"
                )
            self.network.setText("<br>".join(rows))
        else:
            self.network.setText("No network configuration was returned.")

        bios = self._first(data.get("bios"))
        board = self._first(data.get("motherboard"))
        self._hardware_identity = (
            f"BIOS: {bios.get('SMBIOSBIOSVersion', '—')} ({bios.get('Manufacturer', '—')})<br>"
            f"Board: {board.get('Manufacturer', '—')} {board.get('Product', '—')}"
        )
        self.hardware.setText(self._hardware_identity)

        driver_count = len(data.get("drivers", [])) if isinstance(data.get("drivers"), list) else 0
        self.drivers.setText(f"{driver_count} signed-driver records returned by Windows.")
        self.details.setPlainText(json.dumps(data, indent=2, default=str))
        self.subtitle.setText("Live telemetry updates every 2 seconds. Static inventory refreshed successfully.")

    def _inventory_failed(self, error):
        self._inventory_busy = False
        self.refresh_button.setEnabled(True)
        self.subtitle.setText(f"System inventory failed: {error}")
