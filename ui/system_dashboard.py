import json

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QGridLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QVBoxLayout, QWidget, QGroupBox, QTableWidget,
    QTableWidgetItem, QHeaderView,
)

from modules.hardware_monitor import live, sensors
from modules.system_snapshot import snapshot
from modules.startup_manager import records as startup_records
from modules.service_manager import inventory as service_inventory
from modules.services import classify as classify_service


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

    def __init__(self, job_runner, parent=None):
        super().__init__(parent)
        self.jobs = job_runner
        self._closing = False
        self._generation = 0
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

        performance_box = QGroupBox("Performance")
        performance_box.setObjectName("card")
        performance_layout = QGridLayout(performance_box)
        performance_layout.setContentsMargins(12, 14, 12, 12)
        performance_layout.setSpacing(10)
        self.performance_cards = []
        for index in range(8):
            card = MetricCard("Waiting", "—", "waiting for telemetry")
            self.performance_cards.append(card)
            performance_layout.addWidget(card, index // 4, index % 4)
        root.addWidget(performance_box)

        startup_box = QGroupBox("Startup apps")
        startup_box.setObjectName("card")
        startup_layout = QVBoxLayout(startup_box)
        self.startup_summary = QLabel("Loading startup applications…")
        self.startup_summary.setObjectName("muted")
        startup_layout.addWidget(self.startup_summary)
        self.startup_table = QTableWidget(0, 5)
        self.startup_table.setHorizontalHeaderLabels(["Name", "Publisher", "Status", "Source", "Impact"])
        self.startup_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.startup_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.startup_table.verticalHeader().setVisible(False)
        self.startup_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.startup_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.startup_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.startup_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.startup_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self.startup_table.setMaximumHeight(250)
        startup_layout.addWidget(self.startup_table)
        self.service_summary = QLabel("Loading service health…")
        self.service_summary.setObjectName("muted")
        self.service_summary.setWordWrap(True)
        startup_layout.addWidget(self.service_summary)
        root.addWidget(startup_box)

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
        self.network.setTextInteractionFlags(self.network.textInteractionFlags())
        nl.addWidget(self.network)
        self.network_detail = QLabel("Waiting for configuration…")
        self.network_detail.setObjectName("muted")
        self.network_detail.setWordWrap(True)
        nl.addWidget(self.network_detail)
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

        inventory_row = QHBoxLayout()
        inventory_label = QLabel("System inventory is available on demand.")
        inventory_label.setObjectName("muted")
        inventory_row.addWidget(inventory_label)
        inventory_row.addStretch()
        self.inventory_button = QPushButton("View inventory details")
        self.inventory_button.clicked.connect(self._show_inventory_details)
        inventory_row.addWidget(self.inventory_button)
        root.addLayout(inventory_row)

        self._inventory_json = "{}"

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

    @staticmethod
    def _values(value):
        if value is None:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        text = str(value).strip()
        return [text] if text else []

    def _refresh_live(self):
        if self._closing or self._live_busy:
            return
        self._live_busy = True
        generation = self._generation
        signals = self.jobs.submit(live, job_priority=10)
        signals.finished.connect(lambda data, g=generation: self._live_done(data, g))
        signals.failed.connect(lambda error, g=generation: self._live_failed(error, g))

    @staticmethod
    def _rate(value):
        try:
            value = float(value)
        except (TypeError, ValueError):
            return "0 Kbps"
        return f"{value / 1024:.0f} Kbps" if value < 1024 * 1024 else f"{value / 1024 / 1024:.1f} Mbps"

    @staticmethod
    def _card(card, title, value, hint):
        card.setObjectName("metric")
        card.layout().itemAt(0).widget().setText(title.upper())
        card.set_value(value, hint)
        card.show()

    def _live_done(self, data, generation):
        self._live_busy = False
        if self._closing or generation != self._generation:
            return

        cards = self.performance_cards
        for card in cards:
            card.hide()

        cpu = self._first(data.get("cpu"))
        clock = cpu.get("CurrentClockSpeed")
        try:
            clock_text = f"{float(clock) / 1000:.2f} GHz"
        except (TypeError, ValueError):
            clock_text = "—"
        self._card(cards[0], "CPU", f"{cpu.get('LoadPercentage', '—')}%", f"{clock_text} • {cpu.get('Name', 'CPU')}")
        memory = data.get("memory") or {}
        total = float(memory.get("total") or 0)
        used = float(memory.get("used") or 0)
        total_gb = total / 1024**3 if total else 0
        used_gb = used / 1024**3 if used else 0
        self._card(cards[1], "Memory", f"{used_gb:.1f}/{total_gb:.1f} GB", f"{memory.get('percent', 0):.0f}% used")

        disks = data.get("disks") or []
        for index, disk in enumerate(disks[:3], start=2):
            name = disk.get("name") or f"Disk {index - 1}"
            media = disk.get("fstype") or "Local disk"
            active = disk.get("active_percent")
            active_text = f"{float(active):.0f}% active" if active is not None else "activity unavailable"
            self._card(cards[index], name, f"{active_text}", f"{media} • {disk.get('free', 0) / 1024**3:.1f} GB free")

        networks = sorted(data.get("network") or [], key=lambda item: item.get("recv_bps", 0) + item.get("sent_bps", 0), reverse=True)
        if networks:
            net = networks[0]
            self._card(cards[5], net.get("name", "Network"), f"↓ {self._rate(net.get('recv_bps'))}", f"↑ {self._rate(net.get('sent_bps'))}")
        gpus = data.get("gpus") or []
        for index, gpu in enumerate(gpus[:2], start=6):
            name = gpu.get("Name") or f"GPU {index - 6}"
            ram = gpu.get("AdapterRAM")
            ram_text = f"{float(ram) / 1024**3:.1f} GB dedicated" if ram else "Dedicated memory unavailable"
            utilization = gpu.get("utilization")
            value = f"{float(utilization):.0f}%" if utilization is not None else "—"
            self._card(cards[index], f"GPU {index - 6}", value, f"{name} • {ram_text}")


    def _live_failed(self, error, generation):
        self._live_busy = False
        if self._closing or generation != self._generation:
            return
        self.subtitle.setText(f"Live telemetry unavailable: {error}")

    def _refresh_sensors(self):
        if self._closing or self._sensor_busy:
            return
        self._sensor_busy = True
        generation = self._generation
        signals = self.jobs.submit(sensors, job_priority=2)
        signals.finished.connect(lambda data, g=generation: self._sensors_done(data, g))
        signals.failed.connect(lambda error, g=generation: self._sensors_failed(error, g))

    def _sensors_done(self, data, generation):
        self._sensor_busy = False
        if self._closing or generation != self._generation:
            return
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

    def _sensors_failed(self, _error, generation):
        self._sensor_busy = False
        if self._closing or generation != self._generation:
            return

    def _refresh_inventory(self):
        if self._closing or self._inventory_busy:
            return
        self._inventory_busy = True
        self.refresh_button.setEnabled(False)
        generation = self._generation
        self._inventory_pending = 3
        self._inventory_parts = {"snapshot": None, "startup": None, "services": None, "errors": []}
        signals = self.jobs.submit_many([
            (snapshot, (), {}, -2),
            (startup_records, (), {}, -1),
            (service_inventory, (), {}, -1),
        ])
        for role, signal in zip(("snapshot", "startup", "services"), signals):
            signal.finished.connect(lambda value, r=role, g=generation: self._inventory_piece_done(r, value, g))
            signal.failed.connect(lambda error, r=role, g=generation: self._inventory_piece_failed(r, error, g))

    def _inventory_piece_done(self, role, value, generation):
        if self._closing or generation != self._generation:
            return
        self._inventory_parts[role] = value
        self._inventory_pending -= 1
        if self._inventory_pending == 0:
            self._finish_inventory(generation)

    def _inventory_piece_failed(self, role, error, generation):
        if self._closing or generation != self._generation:
            return
        self._inventory_parts["errors"].append(f"{role}: {error}")
        self._inventory_pending -= 1
        if self._inventory_pending == 0:
            self._finish_inventory(generation)

    def _finish_inventory(self, generation):
        self._inventory_busy = False
        if self._closing or generation != self._generation:
            return
        self.refresh_button.setEnabled(True)
        data = self._inventory_parts.get("snapshot") or {}
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
                name = item.get("InterfaceAlias") or item.get("Name") or "Network adapter"
                status = item.get("Status") or "Unknown"
                speed = item.get("LinkSpeed") or "Speed unknown"
                ipv4 = self._values(item.get("IPv4Address"))
                ipv6 = self._values(item.get("IPv6Address"))
                dns = self._values(item.get("DNSServer"))
                gateways = self._values(item.get("IPv4DefaultGateway"))
                row = f"<b>{name}</b> • {status} • {speed}"
                row += f"<br>IPv4: {', '.join(ipv4) if ipv4 else 'None'}"
                if gateways:
                    row += f" • Gateway: {', '.join(gateways)}"
                if ipv6:
                    row += f"<br>IPv6: {', '.join(ipv6[:2])}"
                if dns:
                    row += f"<br>DNS: {', '.join(dns[:3])}"
                rows.append(row)
            self.network.setText("<br><br>".join(rows))
            self.network_detail.setText(f"{len(adapters)} adapter(s) returned by Windows.")
        else:
            self.network.setText("No network adapters returned.")
            self.network_detail.setText("Windows did not return active network configuration.")

        bios = self._first(data.get("bios"))
        board = self._first(data.get("motherboard"))
        self._hardware_identity = (
            f"BIOS: {bios.get('SMBIOSBIOSVersion', '—')} ({bios.get('Manufacturer', '—')})<br>"
            f"Board: {board.get('Manufacturer', '—')} {board.get('Product', '—')}"
        )
        self.hardware.setText(self._hardware_identity)
        driver_count = len(data.get("drivers", [])) if isinstance(data.get("drivers"), list) else 0
        self.drivers.setText(f"{driver_count} signed-driver records returned by Windows.")

        startup = self._inventory_parts.get("startup") or {}
        startup_rows = startup.get("startup", []) if isinstance(startup, dict) else []
        self.startup_table.setRowCount(len(startup_rows))
        for row, item in enumerate(startup_rows):
            values = [
                item.get("Name", "Unknown"),
                item.get("Publisher") or "Unknown",
                item.get("Status") or "Enabled",
                item.get("source", "Other"),
                item.get("impact", "Review"),
            ]
            for col, value in enumerate(values):
                self.startup_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.startup_summary.setText(
            f"{len(startup_rows)} startup applications detected. "
            "This list is separate from Windows services and scheduled tasks."
        )

        service_raw = self._inventory_parts.get("services") or "[]"
        try:
            import json as _json
            service_rows = _json.loads(service_raw)
            if isinstance(service_rows, dict):
                service_rows = [service_rows]
        except (TypeError, ValueError):
            service_rows = []
        running = sum(str(item.get("State", "")).lower() == "running" for item in service_rows)
        automatic = sum(str(item.get("StartMode", "")).lower() == "auto" for item in service_rows)
        disabled = sum(str(item.get("StartMode", "")).lower() == "disabled" for item in service_rows)
        third_party_auto = []
        for item in service_rows:
            if str(item.get("StartMode", "")).lower() != "auto":
                continue
            classification = classify_service(item)
            if classification != "Windows":
                third_party_auto.append(item.get("DisplayName") or item.get("Name") or "Unknown")
        review_names = ", ".join(third_party_auto[:5])
        suffix = f"<br>Review candidates: {review_names}" if review_names else ""
        self.service_summary.setText(
            f"Services: {len(service_rows)} total • {running} running • "
            f"{automatic} automatic • {disabled} disabled. "
            "Third-party automatic services are flagged for review, not automatically classified as bad."
            + suffix
        )

        self._inventory_json = json.dumps(
            {"system": data, "startup": startup, "services": service_rows},
            indent=2,
            default=str,
        )
        errors = self._inventory_parts.get("errors") or []
        if errors:
            self.subtitle.setText("Overview refreshed with warnings: " + " | ".join(errors))
        else:
            self.subtitle.setText("Performance, startup apps and service health refreshed successfully.")


    def _show_inventory_details(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("System inventory details")
        dialog.resize(900, 620)
        layout = QVBoxLayout(dialog)
        label = QLabel(
            "Diagnostic inventory • read-only • generated by the latest system scan."
        )
        label.setObjectName("muted")
        layout.addWidget(label)
        details = QTextEdit()
        details.setReadOnly(True)
        details.setPlainText(self._inventory_json)
        layout.addWidget(details, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dialog.reject)
        buttons.accepted.connect(dialog.accept)
        layout.addWidget(buttons)
        dialog.exec()

    def _inventory_failed(self, error, generation):
        self._inventory_busy = False
        if self._closing or generation != self._generation:
            return
        self.refresh_button.setEnabled(True)
        self.subtitle.setText(f"System inventory failed: {error}")

    def shutdown(self):
        """Stop dashboard timers and invalidate callbacks owned by this view."""
        self._closing = True
        self._generation += 1
        self.timer.stop()
        self.sensor_timer.stop()
