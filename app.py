from pathlib import Path
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMainWindow, QMessageBox, QPushButton,
    QPlainTextEdit, QScrollArea, QStackedWidget, QTextEdit, QVBoxLayout, QWidget, QInputDialog, QFileDialog, QGroupBox, QSizePolicy,
)

from core.backup import BackupManager
from core.logging import get_logger
from core.executor import Executor
from core.jobs import JobRunner
from core.profiles import load_profiles
from core.configuration import build as build_configuration, save as save_configuration, load as load_configuration, export_winget
from core.configuration_engine import compare as compare_configuration, summary as configuration_summary
from core.restore import create_restore_point
from core.profile_execution import execute_approved_plan
from core.recovery import rollback_receipt_item
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
from modules.software import installed_apps, upgrade_all, upgrade_report, upgrade_all_report
from modules.startup import inventory as startup_inventory
from modules.windows_features import inventory as feature_inventory, set_feature
from modules.windows_update import (
    status as update_status,
    reset_components,
    pause_quality,
    pause_feature,
    resume_quality,
    resume_feature,
    set_driver_exclusion,
    set_target_version,
    clear_target_version,
)
from modules.dns_center import inventory as dns_inventory, flush as dns_flush, set_preset as set_dns_preset, PRESETS as DNS_PRESETS
from modules.storage_center import candidates as storage_categories, system_drive as storage_drive
from modules.service_manager import inventory as service_inventory, set_start_mode
from modules.power_center import activate as activate_power, battery_report
from modules.repair_center import component_store_check, component_store_scan, component_store_restore
from ui.appx import AppxPanel
from ui.browser_extensions import BrowserExtensionsPanel
from ui.activity import ActivityPanel
from ui.maintenance import MaintenancePanel
from ui.software import SoftwarePanel
from ui.system_dashboard import SystemDashboard
from ui.windows_management import WindowsManagementPanel
from ui.gaming_center import GamingCenterPanel
from ui.storage_center import StorageCenterPanel
from ui.developer_center import DeveloperCenterPanel
from ui.profile_manager import ProfileManagerDialog


class MainWindow(QMainWindow):
    NAV = (
        ("◉", "Overview"),
        ("✦", "Optimize"),
        ("◫", "Debloat"),
        ("▦", "Install Apps"),
        ("↻", "Updates"),
        ("⚙", "Windows"),
        ("🎮", "Gaming"),
        ("💾", "Storage"),
        ("🛠", "Developer"),
        ("✓", "Fixes"),
        ("◇", "Edge Extensions"),
        ("◷", "Maintenance"),
    )

    def __init__(self):
        super().__init__()
        self.logger = get_logger("gui")
        self.logger.info("Main window created")
        self.setWindowTitle("Windows Optimizer")
        self.resize(1420, 900)
        self.setMinimumSize(1100, 720)
        self.backup = BackupManager()
        self.executor = Executor()
        self.jobs = JobRunner(self)
        self._busy = False
        self._operation_serial = 0
        self._closing = False
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

        brand = QLabel("WINDOWS\nOPTIMIZER")
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
        apps_button.clicked.connect(lambda: self._navigate(3))
        tl.addWidget(apps_button)

        refresh_button = QPushButton("↻")
        refresh_button.setToolTip("Refresh system overview")
        refresh_button.clicked.connect(self.refresh)
        tl.addWidget(refresh_button)
        main_layout.addWidget(topbar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("pageStack")
        self.stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        page_scroll = QScrollArea()
        page_scroll.setObjectName("pageScroll")
        page_scroll.setWidgetResizable(True)
        page_scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        page_scroll.setWidget(self.stack)
        main_layout.addWidget(page_scroll, 1)

        self.activity = ActivityPanel()
        self.output = self.activity.editor
        self.activity.setSizePolicy(
            self.activity.sizePolicy().Policy.Expanding,
            self.activity.sizePolicy().Policy.Minimum,
        )
        main_layout.addWidget(self.activity)
        shell.addWidget(main, 1)

        self._build_pages()
        self._navigate(0)

    def _build_pages(self):
        self.dashboard = SystemDashboard()
        self.stack.addWidget(self.dashboard)
        self._build_tweaks_page()
        self.appx_panel = AppxPanel(self.output, self._run_job)
        self.stack.addWidget(self.appx_panel)
        self.software_panel = SoftwarePanel(self.output, self._run_job)
        self.stack.addWidget(self.software_panel)
        self._build_updates_page()
        self._build_windows_page()
        self.stack.addWidget(GamingCenterPanel(self.output, self._run_job))
        self.stack.addWidget(StorageCenterPanel(self.output, self._run_job, is_admin))
        self.stack.addWidget(DeveloperCenterPanel(self.output, self._run_job, is_admin))
        self._build_repairs_page()
        self.stack.addWidget(BrowserExtensionsPanel(self.output))
        self.stack.addWidget(MaintenancePanel(self.output, self._run_job))

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
        for text, fn, primary in (
            ("Backup", self.create_backup, False),
            ("Restore point", self.restore_point, False),
            ("Profile Manager", self.open_profile_manager, False),
            ("Export config", self.export_configuration, False),
            ("Import config", self.import_configuration, False),
            ("Apply selected", self.apply_selected, True),
        ):
            button = QPushButton(text)
            if primary:
                button.setObjectName("primary")
            button.clicked.connect(fn)
            controls.addWidget(button)
        layout.addLayout(controls)

        self.tweak_tabs = QTabWidget()
        layout.addWidget(self.tweak_tabs)
        self.stack.addWidget(page)

    def _build_updates_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        title = QLabel("Updates & Windows Update")
        title.setObjectName("section")
        layout.addWidget(title)

        label = QLabel(
            "Review update state first. WinGet software upgrades are separate from "
            "Windows Update policy controls. Pauses and target-version policies are "
            "explicit, administrator-only operations."
        )
        label.setObjectName("muted")
        label.setWordWrap(True)
        layout.addWidget(label)

        software = QGroupBox("Software updates")
        software_layout = QVBoxLayout(software)

        summary_row = QHBoxLayout()
        self.update_available_value = QLabel("—")
        self.update_available_value.setObjectName("updateValue")
        self.update_available_hint = QLabel("Not checked")
        self.update_available_hint.setObjectName("muted")
        summary_row.addWidget(self._update_stat("Updates available", self.update_available_value, self.update_available_hint))

        self.update_updated_value = QLabel("—")
        self.update_updated_value.setObjectName("updateValue")
        self.update_updated_hint = QLabel("This run")
        self.update_updated_hint.setObjectName("muted")
        summary_row.addWidget(self._update_stat("Updated", self.update_updated_value, self.update_updated_hint))

        self.update_remaining_value = QLabel("—")
        self.update_remaining_value.setObjectName("updateValue")
        self.update_remaining_hint = QLabel("After upgrade")
        self.update_remaining_hint.setObjectName("muted")
        summary_row.addWidget(self._update_stat("Remaining", self.update_remaining_value, self.update_remaining_hint))
        software_layout.addLayout(summary_row)

        actions = QHBoxLayout()
        scan = QPushButton("Check for updates")
        scan.clicked.connect(self.check_updates)
        actions.addWidget(scan)
        upgrade = QPushButton("Upgrade all")
        upgrade.setObjectName("primary")
        upgrade.clicked.connect(self.upgrade_software)
        actions.addWidget(upgrade)
        actions.addStretch()
        software_layout.addLayout(actions)
        layout.addWidget(software)

        windows = QGroupBox("Windows Update policy")
        windows_layout = QVBoxLayout(windows)

        row = QHBoxLayout()
        for text, fn in (
            ("Refresh status", self.show_update_status),
            ("Pause quality 35d", self.pause_quality_updates),
            ("Resume quality", self.resume_quality_updates),
            ("Pause feature 35d", self.pause_feature_updates),
            ("Resume feature", self.resume_feature_updates),
        ):
            button = QPushButton(text)
            button.clicked.connect(fn)
            row.addWidget(button)
        windows_layout.addLayout(row)

        row2 = QHBoxLayout()
        driver = QPushButton("Exclude drivers")
        driver.clicked.connect(lambda: self.set_update_driver_policy(True))
        row2.addWidget(driver)
        driver_clear = QPushButton("Allow drivers")
        driver_clear.clicked.connect(lambda: self.set_update_driver_policy(False))
        row2.addWidget(driver_clear)
        target = QPushButton("Set target feature version")
        target.clicked.connect(self.set_update_target_version)
        row2.addWidget(target)
        target_clear = QPushButton("Clear target version")
        target_clear.clicked.connect(self.clear_update_target_version)
        row2.addWidget(target_clear)
        row2.addStretch()
        windows_layout.addLayout(row2)

        note = QLabel(
            "Microsoft documents 35-day maximum pause windows for feature and quality "
            "updates. Target release policies should be used deliberately because an "
            "invalid or older target can prevent feature updates until corrected."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        windows_layout.addWidget(note)
        layout.addWidget(windows)

        repair = QGroupBox("Repair")
        repair_layout = QHBoxLayout(repair)
        reset = QPushButton("Reset Windows Update components")
        reset.clicked.connect(self.reset_windows_update)
        repair_layout.addWidget(reset)
        repair_layout.addStretch()
        layout.addWidget(repair)
        layout.addStretch()
        self.stack.addWidget(page)

    @staticmethod
    def _update_stat(title, value_label, hint_label):
        card = QFrame()
        card.setObjectName("updateStat")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 9, 12, 9)
        title_label = QLabel(title.upper())
        title_label.setObjectName("muted")
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        card_layout.addWidget(hint_label)
        return card

    def _build_windows_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        self.windows_management = WindowsManagementPanel(
            self.output, self._run_job, is_admin, parent=page
        )
        layout.addWidget(self.windows_management, 1)

        row = QHBoxLayout()
        for text, fn in (
            ("Windows Optional Features", self.show_features),
            ("Windows Update status", self.show_update_status),
            ("Reset Windows Update", self.reset_windows_update),
        ):
            button = QPushButton(text)
            button.clicked.connect(fn)
            row.addWidget(button)
        layout.addLayout(row)

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
            ("DISM CheckHealth", self.repair_dism_check),
            ("DISM ScanHealth", self.repair_dism_scan),
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
        # Keep refresh lightweight. Page inventory scans are explicit actions.
        self.health.setText("● Ready")
        self.activity.set_ready()
        self.activity.append(
            f"OVERVIEW REFRESHED  {len(self.tweaks)} operations available • "
            f"{sum(t.recommended for t in self.tweaks)} recommended"
        )

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
                try:
                    state_fn = tweak.metadata.get("state") if tweak.metadata else None
                    state = state_fn() if callable(state_fn) else (
                        "APPLIED" if tweak.check and tweak.check() else "NOT APPLIED"
                    )
                except Exception:
                    state = "UNKNOWN"
                detail = QLabel(
                    f"{tweak.description}<br><small>"
                    f"State: {state} • Risk: {tweak.risk} • "
                    f"Reversible: {'Yes' if tweak.reversible else 'No'} • "
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

    def open_profile_manager(self):
        def collect_state():
            features = [item.name for item in feature_inventory() if "Enabled" in item.state]
            return {
                "tweaks": [c.property("tweak_id") for c in self.checks if c.isChecked()],
                "apps": sorted(getattr(self.software_panel, "selected_ids", set())),
                "features": features,
                "power_plan": power_current(),
                "maintenance": {},
            }
        self._run_job(collect_state, done=self._show_profile_manager, fail=self._show_error)

    def _show_profile_manager(self, state):
        def apply_profile(configuration):
            known_tweaks = {t.id for t in self.tweaks}
            known_apps = {a.id for a in __import__("modules.software", fromlist=["CATALOG"]).CATALOG}
            self._set_ids(set(configuration.get("tweaks", [])) & known_tweaks)
            self.software_panel.selected_ids = set(configuration.get("apps", [])) & known_apps
            self.software_panel._render()
            self.loaded_configuration = configuration
            self.output.setPlainText(
                "PROFILE LOADED FOR REVIEW\n"
                "Selections were updated; no Windows changes were applied.\n\n"
                "Use the explicit Apply configuration action when you are ready."
            )

        def execute_profile(profile, selected_items):
            if self._busy:
                return
            if not is_admin():
                QMessageBox.warning(
                    self,
                    "Administrator required",
                    "Run Windows Optimizer as Administrator before executing approved profile operations.",
                )
                return

            self.output.setPlainText(
                f"APPROVED PROFILE EXECUTION\n"
                f"{profile.name} v{profile.version}\n"
                f"Executing {len(selected_items)} approved operation(s)..."
            )
            selected_ids = {(item.kind, item.identifier) for item in selected_items}
            self._run_job(
                execute_approved_plan,
                profile,
                selected_ids,
                self.tweaks,
                done=self._show_profile_execution,
                fail=self._show_error,
            )

        dialog = ProfileManagerDialog(
            self,
            state,
            on_apply=apply_profile,
            on_execute=execute_profile,
        )
        dialog.exec()

    def create_backup(self):
        try:
            path = self.backup.create()
            self.output.setPlainText(f"REGISTRY BACKUP CREATED\n{path}")
            return path
        except Exception as exc:
            self._show_error(exc)

    def export_configuration(self):
        try:
            configuration = build_configuration(
                [c.property("tweak_id") for c in self.checks if c.isChecked()],
                sorted(getattr(self.software_panel, "selected_ids", set())),
                [item.name for item in feature_inventory() if "Enabled" in item.state],
                power_current(),
            )
            path, _ = QFileDialog.getSaveFileName(
                self, "Export WindowsOptimizer configuration", "WindowsOptimizer-config.json", "JSON Files (*.json)"
            )
            if path:
                save_configuration(path, configuration)
                winget = Path(path).with_name(Path(path).stem + "-winget.json")
                export_winget(str(winget))
                self.output.setPlainText(f"CONFIGURATION EXPORTED\n{path}\n{winget}")
        except Exception as exc:
            QMessageBox.critical(self, "Configuration export failed", str(exc))

    def import_configuration(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Import WindowsOptimizer configuration", "", "JSON Files (*.json)"
        )
        if not path:
            return
        try:
            self.loaded_configuration = load_configuration(path)
            self.output.setPlainText(
                f"CONFIGURATION LOADED FOR REVIEW\n{path}\n"
                "No Windows changes were applied. Use Review configuration before applying."
            )
        except Exception as exc:
            QMessageBox.critical(self, "Configuration import failed", str(exc))

    def review_configuration(self):
        if not hasattr(self, "loaded_configuration"):
            QMessageBox.information(self, "No configuration loaded", "Import a WindowsOptimizer configuration first.")
            return
        self._run_job(self._calculate_configuration_diff, done=self._show_configuration_diff, fail=self._show_error)

    def _calculate_configuration_diff(self):
        current_tweaks = [c.property("tweak_id") for c in self.checks if c.isChecked()]
        current_apps = sorted(getattr(self.software_panel, "selected_ids", set()))
        enabled_features = [item.name for item in feature_inventory() if "Enabled" in item.state]
        return compare_configuration(self.loaded_configuration, current_tweaks, current_apps, enabled_features)

    def _show_configuration_diff(self, diff):
        lines = ["CONFIGURATION DIFF", "", configuration_summary(diff)]
        if diff.tweak_select:
            lines.append("Tweaks to select: " + ", ".join(diff.tweak_select))
        if diff.tweak_clear:
            lines.append("Tweaks currently selected but not in profile: " + ", ".join(diff.tweak_clear))
        if diff.apps_install:
            lines.append("Apps to install/select: " + ", ".join(diff.apps_install))
        if diff.features_enable:
            lines.append("Windows features to enable: " + ", ".join(diff.features_enable))
        if diff.apps_unknown:
            lines.append("Unknown apps ignored: " + ", ".join(diff.apps_unknown))
        lines.append("")
        lines.append(
            "Apply config is additive. It does not automatically disable tweaks, remove apps, "
            "or disable Windows features."
        )
        self.output.setPlainText("\n".join(lines))

    def apply_configuration(self):
        if not hasattr(self, "loaded_configuration"):
            QMessageBox.information(self, "No configuration loaded", "Import a WindowsOptimizer configuration first.")
            return
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator before applying a configuration.")
            return
        if QMessageBox.question(
            self,
            "Apply configuration",
            "Apply the additive changes from the loaded configuration? A registry backup will be created first.\n\n"
            "This will not automatically remove apps, disable features, or roll back tweaks absent from the profile.",
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            self.backup.create()
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return
        self._run_job(
            self._apply_configuration_worker,
            done=self._show_configuration_apply,
            fail=self._show_error,
        )

    def _apply_configuration_worker(self):
        from modules.software import install_selected, CATALOG
        desired_tweaks = set(self.loaded_configuration.get("tweaks", []))
        current_tweaks = {c.property("tweak_id") for c in self.checks if c.isChecked()}
        selected = [t for t in self.tweaks if t.id in desired_tweaks - current_tweaks and t.apply]
        results = self.executor.apply(selected) if selected else []
        known_apps = {a.id for a in CATALOG}
        app_ids = [app_id for app_id in self.loaded_configuration.get("apps", []) if app_id in known_apps]
        app_result = install_selected(app_ids) if app_ids else "No application packages selected by the profile."
        enabled = {item.name for item in feature_inventory() if "Enabled" in item.state}
        feature_result = []
        if not is_admin():
            raise RuntimeError("Administrator access is required for Windows feature changes.")
        from modules.windows_features import set_feature
        for name in self.loaded_configuration.get("windows_features", []):
            if name not in enabled:
                feature_result.append(f"{name}: {set_feature(name, True)}")
        return results, app_result, feature_result

    def _show_configuration_apply(self, value):
        results, app_result, feature_result = value
        lines = ["CONFIGURATION APPLY COMPLETE"]
        lines.extend(f"{r.tweak_id}: {r.status} — {r.message} — {r.verification}" for r in results)
        lines.append("\nAPPLICATIONS\n" + app_result)
        lines.append(
            "\nWINDOWS FEATURES\n"
            + ("\n".join(feature_result) if feature_result else "No feature changes required.")
        )
        lines.append("\nNo subtractive changes were made automatically.")
        self.output.setPlainText("\n".join(lines))
        self.refresh()

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

    def _run_job(self, fn, *args, done=None, fail=None, label=None):
        operation = getattr(fn, "__qualname__", repr(fn))
        title = label or operation.split(".")[-1].replace("_", " ").strip().title()
        if self._busy:
            self.logger.warning(
                "Operation rejected because another job is running | operation=%s",
                operation,
            )
            return
        self.logger.info(
            "GUI operation requested | operation=%s | args=%r",
            operation,
            args,
        )
        self._busy = True
        self._operation_serial += 1
        operation_id = self._operation_serial
        self.busy_label.setText(f"● Working…  {title}")
        self.activity.start(title)
        self.activity.append(f"START  {title}")
        signals = self.jobs.submit(fn, *args)

        def finished(value):
            if operation_id != self._operation_serial:
                self.logger.warning("Ignoring stale operation result | id=%s", operation_id)
                return
            self._job_finished(value, done)

        def failed(error):
            if operation_id != self._operation_serial:
                self.logger.warning("Ignoring stale operation error | id=%s", operation_id)
                return
            self._job_failed(error, fail)

        signals.finished.connect(finished)
        signals.failed.connect(failed)

    def _job_finished(self, value, done):
        self.logger.info("GUI operation completed | result_type=%s", type(value).__name__)
        if done:
            done(value)
        summary = self._result_summary(value)
        self.activity.append(f"END    {summary}")
        self.activity.success(self.activity.operation.text(), summary)
        self._job_done()

    def _job_failed(self, error, fail):
        self.logger.error("GUI operation failed | error=%s", error)
        self.activity.append(f"ERROR  {error}")
        if fail:
            fail(error)
        else:
            self._show_error(error)
        self.activity.error(self.activity.operation.text(), error)
        self._job_done()

    @staticmethod
    def _result_summary(value):
        if value is None:
            return "Completed successfully."
        if isinstance(value, str):
            first = next((line.strip() for line in value.splitlines() if line.strip()), "")
            return first[:180] if first else "Completed successfully."
        if isinstance(value, (list, tuple, set)):
            return f"Completed • {len(value)} result item(s)."
        if hasattr(value, "action") and hasattr(value, "available") and hasattr(value, "remaining"):
            if getattr(value, "action", "") == "upgrade":
                return (
                    f"{value.updated} updated • {value.remaining} remaining "
                    f"(started with {value.available})"
                )
            return f"{value.available} app(s) need an update."
        if isinstance(value, dict):
            return f"Completed • {len(value)} result field(s)."
        return f"Completed • {type(value).__name__}."

    def _job_done(self):
        self._busy = False
        self.busy_label.setText("● Ready")

    def _show_result(self, value):
        self.output.setPlainText(str(value))

    def _show_error(self, error):
        self.logger.error("User-visible operation error | %s", error)
        self.output.setPlainText(f"Operation failed:\n{error}")

    def _show_apply_results(self, results):
        self.output.setPlainText(
            "\n".join(
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
            lambda: power_current() + "\n\nAvailable plans:\n" + power_plans(),
            done=self._show_result,
            fail=self._show_error,
        )

    def show_power_center(self):
        self._run_job(
            lambda: power_current() + "\n\n" + power_plans(),
            done=self._show_result,
            fail=self._show_error,
        )

    def change_power_plan(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        plan, ok = QInputDialog.getItem(
            self,
            "Power plan",
            "Plan:",
            ["Balanced", "Power saver", "High performance"],
            0,
            False,
        )
        if not ok:
            return
        if QMessageBox.question(self, "Confirm power plan", f"Activate {plan}?") != QMessageBox.StandardButton.Yes:
            return
        self._run_job(activate_power, plan, done=self._show_result, fail=self._show_error)

    def generate_battery_report(self):
        self._run_job(battery_report, done=self._show_result, fail=self._show_error)

    def show_service_inventory(self):
        self._run_job(service_inventory, done=self._show_result, fail=self._show_error)

    def change_service_mode(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        name, ok = QInputDialog.getText(self, "Service startup", "Exact service Name:")
        if not ok or not name.strip():
            return
        mode, ok = QInputDialog.getItem(
            self, "Startup mode", "Mode:", ["Automatic", "Manual", "Disabled"], 1, False
        )
        if not ok:
            return
        if QMessageBox.question(
            self,
            "Confirm service change",
            f"Set '{name.strip()}' to {mode}?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_job(set_start_mode, name.strip(), mode, done=self._show_result, fail=self._show_error)

    def show_dns(self):
        self._run_job(dns_inventory, done=self._show_result, fail=self._show_error)

    def change_dns(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        index, ok = QInputDialog.getInt(self, "DNS interface", "Interface index:", 1, 1, 65535)
        if not ok:
            return
        preset, ok = QInputDialog.getItem(
            self, "DNS preset", "Preset:", list(DNS_PRESETS), 0, False
        )
        if not ok:
            return
        if QMessageBox.question(
            self,
            "Confirm DNS change",
            f"Apply '{preset}' to interface {index}?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_job(set_dns_preset, index, preset, done=self._show_result, fail=self._show_error)

    def flush_dns(self):
        self._run_job(dns_flush, done=self._show_result, fail=self._show_error)

    def show_storage(self):
        def report():
            drive = storage_drive()
            items = storage_categories()
            return (
                "STORAGE\n"
                + f"System drive: {drive['free']/1024**3:.1f} GB free / {drive['total']/1024**3:.1f} GB\n\n"
                + "\n".join(
                    f"{x.name}: {x.size_bytes/1024**3:.2f} GB — {x.path}"
                    for x in items
                )
            )

        self._run_job(report, done=self._show_result, fail=self._show_error)

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
        self._navigate(3)
        self.software_panel.focus_search()

    def upgrade_software(self):
        self._run_job(
            upgrade_all_report,
            done=self._show_upgrade_report,
            fail=self._show_error,
            label="Upgrade all • WinGet (may take several minutes)",
        )

    def check_updates(self):
        self._run_job(
            upgrade_report,
            done=self._show_update_report,
            fail=self._show_error,
            label="Checking installed apps for updates",
        )

    def _show_update_report(self, report):
        self.update_available_value.setText(str(report.available))
        self.update_available_hint.setText("apps need an update" if report.available != 1 else "app needs an update")
        self.update_updated_value.setText("—")
        self.update_updated_hint.setText("Run Upgrade all to update")
        self.update_remaining_value.setText(str(report.remaining))
        self.update_remaining_hint.setText("currently available")
        self.output.setPlainText(report.output or "No upgrades available.")
        self.activity.append(
            f"UPDATES  {report.available} app(s) need an update"
        )

    def _show_upgrade_report(self, report):
        self.update_available_value.setText(str(report.available))
        self.update_available_hint.setText("found before upgrade")
        self.update_updated_value.setText(str(report.updated))
        self.update_updated_hint.setText("updated successfully" if report.updated != 1 else "updated successfully")
        self.update_remaining_value.setText(str(report.remaining))
        self.update_remaining_hint.setText(
            "All clear" if report.remaining == 0 else "still need attention"
        )
        self.output.setPlainText(report.output or "WinGet completed.")
        self.activity.append(
            f"UPGRADE  {report.updated} updated • {report.remaining} remaining"
        )

    def repair_explorer(self):
        self._run_job(explorer, done=self._show_result, fail=self._show_error)

    def show_features(self):
        self._run_job(feature_inventory, done=self._show_features, fail=self._show_error)

    def _show_features(self, features):
        enabled = [f for f in features if "Enabled" in f.state]
        self.output.setPlainText(
            "WINDOWS OPTIONAL FEATURES\n"
            + f"{len(features)} feature(s) • {len(enabled)} currently enabled\n\n"
            + "\n".join(
                f"{f.name} | {f.display_name} | {f.state}"
                + (" | restart" if f.restart_required else "")
                for f in features[:120]
            )
        )

    def change_feature(self, enable):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        name, accepted = QInputDialog.getText(
            self,
            "Windows Optional Feature",
            "Enter the exact FeatureName returned by inventory:",
        )
        if not accepted or not name.strip():
            return
        action = "Enable" if enable else "Disable"
        if QMessageBox.question(
            self,
            f"{action} feature",
            f"{action} '{name.strip()}'? A restart may be required.",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_job(
            set_feature,
            name.strip(),
            enable,
            done=self._show_result,
            fail=self._show_error,
        )

    def _run_update_change(self, fn, *args):
        try:
            backup = self.backup.create()
        except Exception as exc:
            QMessageBox.critical(self, "Backup failed", str(exc))
            return
        self.output.setPlainText(f"WINDOWS UPDATE BACKUP\n{backup}")
        self._run_job(fn, *args, done=self._show_result, fail=self._show_error)

    def pause_quality_updates(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        if QMessageBox.question(
            self,
            "Pause quality updates",
            "Pause Windows quality updates for up to 35 days from today?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_update_change(pause_quality)

    def resume_quality_updates(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        self._run_update_change(resume_quality)

    def pause_feature_updates(self):
        if not is_admin():
            QMessageBox.warning(self, "Pause feature updates", "Run as Administrator.")
            return
        if QMessageBox.question(
            self,
            "Pause feature updates",
            "Pause Windows feature updates for up to 35 days from today?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_update_change(pause_feature)

    def resume_feature_updates(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        self._run_update_change(resume_feature)

    def set_update_driver_policy(self, enabled):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        action = "exclude" if enabled else "allow"
        if QMessageBox.question(
            self,
            "Windows Update drivers",
            f"{action.title()} driver packages from normal Windows Update quality-update delivery?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_update_change(set_driver_exclusion, enabled)

    def set_update_target_version(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        version, ok = QInputDialog.getText(
            self, "Target feature version", "Windows release (example: 25H2):"
        )
        if not ok or not version.strip():
            return
        if QMessageBox.question(
            self,
            "Target feature version",
            f"Keep Windows Update on Windows 11 {version.strip()} until this policy is changed?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_update_change(set_target_version, version.strip())

    def clear_update_target_version(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        if QMessageBox.question(
            self,
            "Clear target version",
            "Clear the configured Windows Update target feature version?",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_update_change(clear_target_version)

    def show_update_status(self):
        self._run_job(update_status, done=self._show_result, fail=self._show_error)

    def reset_windows_update(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        if QMessageBox.question(
            self,
            "Reset Windows Update",
            "Stop Windows Update services and rename their cache folders? The original folders are retained for recovery.",
        ) != QMessageBox.StandardButton.Yes:
            return
        self._run_job(reset_components, done=self._show_result, fail=self._show_error)

    def repair_dism_check(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        self._run_job(component_store_check, done=self._show_result, fail=self._show_error)

    def repair_dism_scan(self):
        if not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator.")
            return
        self._run_job(component_store_scan, done=self._show_result, fail=self._show_error)

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
