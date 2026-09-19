from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QTextEdit, QVBoxLayout, QWidget,
)

from core.backup import BackupManager
from core.executor import Executor
from core.jobs import JobRunner
from core.profiles import load_profiles
from core.restore import create_restore_point
from core.system_info import is_admin
from modules.catalog import all_tweaks
from modules.network_center import (
    adapters as network_adapters,
    configuration as network_configuration,
    latency as network_latency,
)
from modules.power import current as power_current, plans as power_plans, set_high_performance
from modules.repair import dism, explorer, sfc
from modules.services import inventory as services_inventory
from modules.software import installed_apps, upgrade_all
from modules.startup import inventory as startup_inventory
from ui.browser_extensions import BrowserExtensionsPanel
from ui.maintenance import MaintenancePanel
from ui.software import SoftwarePanel
from ui.system_dashboard import SystemDashboard


class MainWindow(QMainWindow):
    NAV = (
        ("◉", "Overview"),
        ("✦", "Optimize"),
        ("▦", "Install Apps"),
        ("↻", "Updates"),
        ("⚙", "Windows"),
        ("✓", "Fixes"),
        ("◇", "Edge Extensions"),
        ("◷", "Maintenance"),
    )

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Windows Optimizer")
        self.resize(1420, 900)
        self.setMinimumSize(1100, 720)
        self.backup = BackupManager()
        self.executor = Executor()
        self.jobs = JobRunner(self)
        self._busy = False
        self._build_ui()
        self.refresh()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        shell = QHBoxLayout(root)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(214)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(16, 20, 16, 18)
        sl.setSpacing(6)

        brand = QLabel("WINDOWS
OPTIMIZER")
        brand.setStyleSheet("font-size:16pt;font-weight:800;letter-spacing:1px;color:#f5f8fc;")
        sl.addWidget(brand)
        sub = QLabel("SYSTEM CONTROL CENTER")
        sub.setObjectName("muted")
        sl.addWidget(sub)
        sl.addSpacing(18)

        self.nav_buttons = []
        for index, (icon, label) in enumerate(self.NAV):
            button = QPushButton(f"  {icon}   {label}")
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked, i=index: self._navigate(i))
            sl.addWidget(button)
            self.nav_buttons.append(button)
        sl.addStretch()

        self.health = QLabel("●  Starting…")
        self.health.setObjectName("muted")
        sl.addWidget(self.health)
        shell.addWidget(sidebar)

        main = QFrame()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        topbar = QFrame()
        topbar.setObjectName("topbar")
        tl = QHBoxLayout(topbar)
        tl.setContentsMargins(24, 14, 24, 14)

        title_box = QVBoxLayout()
        title = QLabel("Windows Optimizer")
        title.setObjectName("section")
        self.page_title = QLabel("Overview")
        self.page_title.setObjectName("muted")
        title_box.addWidget(title)
        title_box.addWidget(self.page_title)
        tl.addLayout(title_box)
        tl.addStretch()

        self.busy_label = QLabel("● Ready")
        self.busy_label.setObjectName("muted")
        tl.addWidget(self.busy_label)
        self.admin = QLabel("Standard user")
        self.admin.setObjectName("muted")
        tl.addWidget(self.admin)

        apps_button = QPushButton("Install Apps")
        apps_button.setObjectName("primary")
        apps_button.clicked.connect(lambda: self._navigate(2))
        tl.addWidget(apps_button)

        refresh_button = QPushButton("↻")
        refresh_button.setToolTip("Refresh system overview")
        refresh_button.clicked.connect(self.refresh)
        tl.addWidget(refresh_button)
        main_layout.addWidget(topbar)

        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMaximumHeight(115)
        self.output.setPlaceholderText("Operation log")
        main_layout.addWidget(self.output)
        shell.addWidget(main, 1)

        self._build_pages()
        self._navigate(0)

    def _build_pages(self):
        self.dashboard = SystemDashboard()
        self.stack.addWidget(self.dashboard)
        self._build_tweaks_page()
        self.software_panel = SoftwarePanel(self.output, self._run_job)
        self.stack.addWidget(self.software_panel)
        self._build_updates_page()
        self._build_windows_page()
        self._build_repairs_page()
        self.stack.addWidget(BrowserExtensionsPanel(self.output))
        self.stack.addWidget(MaintenancePanel(self.output))

    def _build_tweaks_page(self):
        from PySide6.QtWidgets import QCheckBox, QComboBox, QGroupBox, QScrollArea, QTabWidget

        page = QWidget()
        layout = QVBoxLayout(page)
        intro = QLabel(
            "Choose explicit Windows changes. Every operation carries risk, "
            "reversibility and restart metadata."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        layout.addWidget(intro)

        controls = QHBoxLayout()
        self.profile = QComboBox()
        self.profile.addItem("Custom", None)
        for profile in load_profiles():
            self.profile.addItem(profile.get("name", profile["id"]), profile)
        self.profile.currentIndexChanged.connect(self.select_profile)
        controls.addWidget(self.profile)

        for text, fn in (("Recommended", self.select_recommended), ("Clear", self.clear_selection)):
            button = QPushButton(text)
            button.clicked.connect(fn)
            controls.addWidget(button)
        controls.addStretch()
        layout.addLayout(controls)

        self.tweak_tabs = QTabWidget()
        layout.addWidget(self.tweak_tabs)
        self.stack.addWidget(page)

    def _build_updates_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Software updates")
        title.setObjectName("section")
        layout.addWidget(title)
        label = QLabel(
            "Review the WinGet upgrade inventory before applying upgrades. "
            "Automatic daily upgrades are intentionally not part of SYSTEM maintenance."
        )
        label.setObjectName("muted")
        label.setWordWrap(True)
        layout.addWidget(label)

        scan = QPushButton("Check available upgrades")
        scan.clicked.connect(self.check_updates)
        layout.addWidget(scan)

        upgrade = QPushButton("Upgrade all")
        upgrade.setObjectName("primary")
        upgrade.clicked.connect(self.upgrade_software)
        layout.addWidget(upgrade)
        layout.addStretch()
        self.stack.addWidget(page)

    def _build_windows_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Windows management")
        title.setObjectName("section")
        layout.addWidget(title)
        info = QLabel(
            "Diagnostics first. System-wide changes are explicit and guarded "
            "instead of bundled into a blind preset."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        row = QHBoxLayout()
        actions = (
            ("Startup inventory", self.show_startup),
            ("Services", self.show_services),
            ("Power plans", self.show_power),
            ("Network adapters", self.show_network),
            ("Network config", self.show_network_config),
            ("Ping 1.1.1.1", self.show_latency),
        )
        for text, fn in actions:
            button = QPushButton(text)
            button.clicked.connect(fn)
            row.addWidget(button)
        layout.addLayout(row)

        high = QPushButton("Activate High Performance power plan")
        high.clicked.connect(self.enable_high_performance)
        layout.addWidget(high)
        layout.addStretch()
        self.stack.addWidget(page)

    def _build_repairs_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("Fixes & repair")
        title.setObjectName("section")
        layout.addWidget(title)
        label = QLabel(
            "Use repair tools for troubleshooting. SFC/DISM can take several "
            "minutes and are not routine performance tweaks."
        )
        label.setObjectName("muted")
        label.setWordWrap(True)
        layout.addWidget(label)

        for text, fn in (
            ("Restart Explorer", self.repair_explorer),
            ("Run SFC /scannow", self.repair_sfc),
            ("Run DISM RestoreHealth", self.repair_dism),
        ):
            button = QPushButton(text)
            button.clicked.connect(fn)
            layout.addWidget(button)
        layout.addStretch()
        self.stack.addWidget(page)

    def _navigate(self, index):
        self.stack.setCurrentIndex(index)
        for i, button in enumerate(self.nav_buttons):
            button.setChecked(i == index)
        self.page_title.setText(self.NAV[index][1])

    def refresh(self):
        self.admin.setText("Administrator" if is_admin() else "Standard user")
        self.tweaks = all_tweaks()
        self._render_tweaks()
        self.health.setText("● Live dashboard")
        self.output.setPlainText(
            f"SCAN COMPLETE
{len(self.tweaks)} operations available • "
            f"{sum(t.recommended for t in self.tweaks)} recommended"
        )
        if hasattr(self, "dashboard"):
            self.dashboard._refresh_inventory()

    def _render_tweaks(self):
        from PySide6.QtWidgets import QCheckBox, QGroupBox, QScrollArea, QVBoxLayout, QWidget

        self.tweak_tabs.clear()
        self.checks = []
        groups = {}
        for tweak in self.tweaks:
            groups.setdefault(tweak.category, []).append(tweak)

        for category, items in groups.items():
            page = QWidget()
            layout = QVBoxLayout(page)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            inner = QWidget()
            inner_layout = QVBoxLayout(inner)

            for tweak in items:
                box = QGroupBox()
                box.setObjectName("card")
                box_layout = QVBoxLayout(box)
                check = QCheckBox(tweak.name)
                check.setChecked(tweak.recommended)
                check.setProperty("tweak_id", tweak.id)
                box_layout.addWidget(check)
                detail = QLabel(
                    f"{tweak.description}<br><small>"
                    f"Risk: {tweak.risk} • Reversible: {'Yes' if tweak.reversible else 'No'} • "
                    f"Restart: {tweak.restart}</small>"
                )
                detail.setWordWrap(True)
                box_layout.addWidget(detail)
                inner_layout.addWidget(box)
                self.checks.append(check)

            inner_layout.addStretch()
            scroll.setWidget(inner)
            layout.addWidget(scroll)
            self.tweak_tabs.addTab(page, category)

    def _set_ids(self, ids):
        ids = set(ids)
        for check in self.checks:
            check.setChecked(check.property("tweak_id") in ids)

    def select_profile(self, index):
        profile = self.profile.itemData(index)
        if profile:
            self._set_ids(profile.get("tweaks", []))

    def select_recommended(self):
        self._set_ids(t.id for t in self.tweaks if t.recommended)

    def clear_selection(self):
        self._set_ids([])

    def create_backup(self):
        try:
            self.output.setPlainText(f"BACKUP CREATED
{self.backup.create()}")
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))

    def restore_point(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run Windows Optimizer as Administrator.")
            return
        self._run_job(create_restore_point, done=self._show_result, fail=self._show_error)

    def apply_selected(self):
        if self._busy:
            return
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator before applying changes.")
            return

        ids = {c.property("tweak_id") for c in self.checks if c.isChecked()}
        selected = [t for t in self.tweaks if t.id in ids and t.apply]
        if not selected:
            QMessageBox.information(self, "Nothing selected", "Select at least one tweak.")
            return

        if QMessageBox.question(
            self,
            "Confirm changes",
            f"Apply {len(selected)} selected operation(s)? A registry backup will be created first.",
        ) != QMessageBox.StandardButton.Yes:
            return

        try:
            self.backup.create()
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return

        self._run_job(self.executor.apply, selected, done=self._show_apply_results, fail=self._show_error)

    def _run_job(self, fn, *args, done=None, fail=None):
        if self._busy:
            return
        self._busy = True
        self.busy_label.setText("● Working…")
        signals = self.jobs.submit(fn, *args)
        signals.finished.connect(lambda value: self._job_finished(value, done))
        signals.failed.connect(lambda error: self._job_failed(error, fail))

    def _job_finished(self, value, done):
        if done:
            done(value)
        self._job_done()

    def _job_failed(self, error, fail):
        if fail:
            fail(error)
        self._job_done()

    def _job_done(self):
        self._busy = False
        self.busy_label.setText("● Ready")

    def _show_result(self, value):
        self.output.setPlainText(str(value))

    def _show_error(self, error):
        self.output.setPlainText(f"Operation failed:
{error}")

    def _show_apply_results(self, results):
        self.output.setPlainText(
            "
".join(
                f"{result.tweak_id}: {result.status} — {result.message} — {result.verification}"
                for result in results
            )
        )
        self.dashboard._refresh_inventory()

    def show_startup(self):
        self._run_job(startup_inventory, done=self._show_result, fail=self._show_error)

    def show_services(self):
        self._run_job(services_inventory, done=self._show_result, fail=self._show_error)

    def show_power(self):
        self._run_job(
            lambda: power_current() + "

Available plans:
" + power_plans(),
            done=self._show_result,
            fail=self._show_error,
        )

    def show_network(self):
        self._run_job(network_adapters, done=self._show_result, fail=self._show_error)

    def show_network_config(self):
        self._run_job(network_configuration, done=self._show_result, fail=self._show_error)

    def show_latency(self):
        self._run_job(network_latency, done=self._show_result, fail=self._show_error)

    def enable_high_performance(self):
        if not is_admin():
            QMessageBox.warning(
                self,
                "Administrator required",
                "Run as Administrator to change the active power plan.",
            )
            return
        if QMessageBox.question(
            self,
            "Power plan",
            "Activate High Performance for this Windows installation?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_job(set_high_performance, done=self._show_result, fail=self._show_error)

    def show_software(self):
        self._run_job(installed_apps, done=self._show_result, fail=self._show_error)

    def install_selected(self, item=None):
        self._navigate(2)
        self.software_panel.focus_search()

    def upgrade_software(self):
        self._run_job(upgrade_all, done=self._show_result, fail=self._show_error)

    def check_updates(self):
        from modules.software import upgrade_available
        self._run_job(upgrade_available, done=self._show_result, fail=self._show_error)

    def repair_explorer(self):
        self._run_job(explorer, done=self._show_result, fail=self._show_error)

    def repair_sfc(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        self._run_job(sfc, done=self._show_result, fail=self._show_error)

    def repair_dism(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        self._run_job(dism, done=self._show_result, fail=self._show_error)
