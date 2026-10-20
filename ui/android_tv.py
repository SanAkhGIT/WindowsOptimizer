"""PySide6 Android TV workspace: read-first diagnostics and confirmed ADB actions."""
import json
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QTextEdit, QVBoxLayout,
    QWidget,
)

from modules import android_tv as tv


class AndroidTvPanel(QWidget):
    """ADB TV controls kept separate from Windows tweaks and Windows debloat."""

    def __init__(self, output, run_job, parent=None):
        super().__init__(parent)
        self.output = output
        self.run_job = run_job
        self._layout_loaded = False
        self._layout_readable = False
        self._candidate_data = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 12)
        root.setSpacing(12)

        title = QLabel("Android TV Control Center")
        title.setObjectName("title")
        root.addWidget(title)
        intro = QLabel(
            "Manage Android/Google TV through ADB: inspect the device, review optional packages, "
            "apply reversible UI settings, and manage the Home launcher. Nothing is uninstalled. "
            "Every device mutation requires confirmation and is recorded in a local undo journal."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        root.addWidget(intro)

        connection = QGroupBox("ADB connection")
        form = QFormLayout(connection)
        self.ip_edit = QLineEdit("192.168.0.21")
        self.ip_edit.setPlaceholderText("TV IP address")
        self.port_edit = QLineEdit("5555")
        self.port_edit.setMaximumWidth(120)
        self.adb_edit = QLineEdit(self._default_adb())
        self.adb_edit.setPlaceholderText("Full path to adb.exe")
        browse = QPushButton("Browse…")
        browse.clicked.connect(self._browse_adb)
        adb_row = QHBoxLayout()
        adb_row.addWidget(self.adb_edit, 1)
        adb_row.addWidget(browse)
        adb_widget = QWidget()
        adb_widget.setLayout(adb_row)
        form.addRow("TV IP", self.ip_edit)
        form.addRow("ADB TCP port", self.port_edit)
        form.addRow("ADB executable", adb_widget)
        actions = QHBoxLayout()
        self.connection_status = QLabel("Not checked")
        self.connection_status.setObjectName("pageStatus")
        connect_button = QPushButton("Connect")
        connect_button.setObjectName("primary")
        connect_button.clicked.connect(self.connect_device)
        scan_button = QPushButton("Read device health")
        scan_button.clicked.connect(self.scan_health)
        actions.addWidget(self.connection_status, 1)
        actions.addWidget(connect_button)
        actions.addWidget(scan_button)
        form.addRow("", actions)
        root.addWidget(connection)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self._build_health_tab()
        self._build_debloat_tab()
        self._build_optimization_tab()
        self._build_launcher_tab()

    @staticmethod
    def _default_adb():
        try:
            return tv._adb_path()
        except Exception:
            return ""

    def _browse_adb(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Google Android Platform-Tools adb.exe", self.adb_edit.text(),
            "ADB executable (adb.exe);;All files (*.*)",
        )
        if path:
            self.adb_edit.setText(path)

    def _params(self):
        ip = self.ip_edit.text().strip()
        port_text = self.port_edit.text().strip()
        try:
            port = int(port_text)
        except ValueError as exc:
            raise ValueError("ADB TCP port must be a number, usually 5555.") from exc
        adb = self.adb_edit.text().strip() or None
        return {"tv_ip": ip, "port": port, "adb_path": adb}

    def _async(self, label, fn):
        try:
            params = self._params()
        except Exception as exc:
            QMessageBox.warning(self, "Connection details", str(exc))
            return
        self.connection_status.setText(f"Working: {label}…")
        def task():
            return fn(**params)
        self.run_job(
            task,
            done=lambda result: self._show_result(label, result),
            fail=lambda error: self._show_error(label, error),
            label=label,
        )

    def _show_result(self, label, result):
        self.connection_status.setText(f"Complete: {label}")
        if isinstance(result, (dict, list)):
            rendered = json.dumps(result, indent=2, ensure_ascii=False)
        else:
            rendered = str(result)
        self.output.setPlainText(rendered)
        self._show_detail(rendered)

    def _show_error(self, label, error):
        message = str(error)
        self.connection_status.setText(f"Failed: {label}")
        self.output.setPlainText(f"{label} failed:\n{message}")
        self._show_detail(f"{label} failed:\n{message}")

    def _show_detail(self, value):
        if hasattr(self, "details"):
            self.details.setPlainText(value)

    def _build_health_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        info = QLabel(
            "Health scans are read-only. They report the actual Home activity, disabled packages, "
            "memory (including MemAvailable), private DNS, animation settings, and background state "
            "for common TV apps."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)
        buttons = QHBoxLayout()
        scan = QPushButton("Scan health")
        scan.clicked.connect(self.scan_health)
        settings = QPushButton("Open Android Settings")
        settings.clicked.connect(self.open_settings)
        undo = QPushButton("Undo latest reversible change")
        undo.clicked.connect(self.undo_last)
        buttons.addWidget(scan)
        buttons.addWidget(settings)
        buttons.addStretch()
        buttons.addWidget(undo)
        layout.addLayout(buttons)
        self.details = QTextEdit()
        self.details.setReadOnly(True)
        self.details.setPlaceholderText("Connect and scan to view the TV report.")
        self.details.setMinimumHeight(230)
        layout.addWidget(self.details, 1)
        self.tabs.addTab(page, "Device health")

    def _build_debloat_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        info = QLabel(
            "Only reviewed optional-package candidates are listed. Items are never preselected or bulk-disabled. "
            "Select one package to see its purpose, then confirm each disable/restore separately. "
            "Protected Android, Google Play, input, System UI, Settings, and device-vendor packages are not actionable here."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)
        row = QHBoxLayout()
        refresh = QPushButton("Refresh candidate list")
        refresh.clicked.connect(self.refresh_candidates)
        disable = QPushButton("Disable selected")
        disable.setObjectName("primary")
        disable.clicked.connect(lambda: self.change_selected_package(False))
        enable = QPushButton("Restore selected")
        enable.clicked.connect(lambda: self.change_selected_package(True))
        row.addWidget(refresh)
        row.addStretch()
        row.addWidget(disable)
        row.addWidget(enable)
        layout.addLayout(row)
        self.candidate_table = QTableWidget(0, 3)
        self.candidate_table.setHorizontalHeaderLabels(["Package", "Current state", "Purpose / trade-off"])
        self.candidate_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.candidate_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.candidate_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.candidate_table.verticalHeader().setVisible(False)
        self.candidate_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.candidate_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.candidate_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.candidate_table, 1)
        self.tabs.addTab(page, "Debloat")

    def _build_optimization_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)
        info = QLabel(
            "Reversible settings capture their exact prior values in the undo journal. Cache trimming and "
            "ART compilation have no exact inverse; they are separate, optional maintenance operations."
        )
        info.setObjectName("muted")
        info.setWordWrap(True)
        layout.addWidget(info)

        ui_group = QGroupBox("UI responsiveness")
        ui_layout = QVBoxLayout(ui_group)
        anim_row = QHBoxLayout()
        anim_label = QLabel("Set the three Android animation scales to 0 for a snappier interface.")
        anim_label.setWordWrap(True)
        anim_button = QPushButton("Disable animations")
        anim_button.setObjectName("primary")
        anim_button.clicked.connect(self.disable_animations)
        anim_row.addWidget(anim_label, 1)
        anim_row.addWidget(anim_button)
        ui_layout.addLayout(anim_row)

        saver_row = QHBoxLayout()
        saver_label = QLabel("Disable the Android screensaver setting. This may change idle-screen behavior.")
        saver_label.setWordWrap(True)
        saver_button = QPushButton("Disable screensaver")
        saver_button.clicked.connect(self.turn_off_screensaver)
        saver_row.addWidget(saver_label, 1)
        saver_row.addWidget(saver_button)
        ui_layout.addLayout(saver_row)
        layout.addWidget(ui_group)

        maintenance = QGroupBox("Optional maintenance — no automatic undo")
        maintenance_layout = QVBoxLayout(maintenance)
        cache_row = QHBoxLayout()
        cache_label = QLabel("Trim package caches to free up space. Caches may rebuild and apps may load more slowly.")
        cache_label.setWordWrap(True)
        cache_button = QPushButton("Trim caches")
        cache_button.clicked.connect(self.trim_caches)
        cache_row.addWidget(cache_label, 1)
        cache_row.addWidget(cache_button)
        maintenance_layout.addLayout(cache_row)
        compile_row = QHBoxLayout()
        compile_label = QLabel("Ask ART to compile installed packages with speed-profile; firmware support and benefit vary.")
        compile_label.setWordWrap(True)
        compile_button = QPushButton("Compile apps")
        compile_button.clicked.connect(self.compile_apps)
        compile_row.addWidget(compile_label, 1)
        compile_row.addWidget(compile_button)
        maintenance_layout.addLayout(compile_row)
        layout.addWidget(maintenance)
        layout.addStretch(1)
        self.tabs.addTab(page, "Optimization")

    def _build_launcher_tab(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        note = QLabel(
            "tv-detox is the reference launcher. Launcher switching is verified and rolled back on failure; "
            "the stock launcher is never disabled by the tv-detox action. Restoring Google TV Home enables "
            "only the Google TV launcher and leaves the setup package untouched."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        # One unified launcher workflow. FIZXIX Home is the default branded option;
        # official TV Detox remains available for users who explicitly choose it.
        launcher_group = QGroupBox("Home launcher")
        launcher_layout = QVBoxLayout(launcher_group)
        launcher_choice_row = QHBoxLayout()
        launcher_choice_row.addWidget(QLabel("Preferred launcher:"))
        self.install_target = QComboBox()
        self.install_target.addItem("FIZXIX Home — black background + watermark", tv.FIZXIX_HOME_PACKAGE)
        self.install_target.addItem("Official TV Detox", tv.TV_DETOX_PACKAGE)
        launcher_choice_row.addWidget(self.install_target, 1)
        launcher_layout.addLayout(launcher_choice_row)

        launcher_help = QLabel(
            "FIZXIX Home is the recommended branded launcher. Install/update and Home switching are "
            "handled here alongside device health and optimization. Google TV Home remains installed "
            "so you can restore it at any time."
        )
        launcher_help.setObjectName("muted")
        launcher_help.setWordWrap(True)
        launcher_layout.addWidget(launcher_help)

        actions = QHBoxLayout()
        install = QPushButton("Install / update selected launcher…")
        install.setObjectName("primary")
        install.clicked.connect(self.install_selected_launcher)
        make_home = QPushButton("Set selected launcher as Home")
        make_home.clicked.connect(self.set_selected_launcher_home)
        stock = QPushButton("Restore Google TV Home")
        stock.clicked.connect(self.restore_stock_home)
        settings = QPushButton("Open Settings")
        settings.clicked.connect(self.open_settings)
        actions.addWidget(install)
        actions.addWidget(make_home)
        actions.addWidget(stock)
        actions.addWidget(settings)
        launcher_layout.addLayout(actions)
        layout.addWidget(launcher_group)

        custom = QGroupBox("Launcher app tiles and shortcuts")
        custom_layout = QVBoxLayout(custom)
        explain = QLabel(
            "Load the current layout first. If the official release APK blocks preference readback, you can still "
            "edit from WindowsOptimizer by entering an exact manual snapshot of the current tile order and shortcuts. "
            "The snapshot becomes the Undo state, so only use values you have verified on the TV."
        )
        explain.setObjectName("muted")
        explain.setWordWrap(True)
        custom_layout.addWidget(explain)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Launcher layout to edit:"))
        self.launcher_target = QComboBox()
        self.launcher_target.addItem("Official TV Detox", tv.TV_DETOX_PACKAGE)
        self.launcher_target.addItem("FIZXIX Home (black + watermark)", tv.FIZXIX_HOME_PACKAGE)
        self.launcher_target.currentIndexChanged.connect(self._launcher_target_changed)
        target_row.addWidget(self.launcher_target, 1)
        custom_layout.addLayout(target_row)

        self.manual_backup_toggle = QCheckBox(
            "Use a verified manual snapshot if tv-detox does not expose its saved preferences"
        )
        self.manual_backup_toggle.setEnabled(False)
        self.manual_backup_toggle.toggled.connect(self._manual_backup_changed)
        custom_layout.addWidget(self.manual_backup_toggle)

        self.manual_backup_group = QGroupBox("Snapshot of the CURRENT TV layout (before applying changes)")
        manual_layout = QVBoxLayout(self.manual_backup_group)
        manual_help = QLabel(
            "Enter current app package IDs in the exact order shown on tv-detox, or explicitly confirm that "
            "the current app row uses automatic discovery. Select current Bluetooth/Sound/Picture shortcuts too. "
            "These values are used as the rollback snapshot when the APK prevents automatic readback."
        )
        manual_help.setObjectName("muted")
        manual_help.setWordWrap(True)
        manual_layout.addWidget(manual_help)
        self.manual_current_auto = QCheckBox("Current app tiles use automatic discovery")
        self.manual_current_auto.toggled.connect(self._manual_current_auto_changed)
        manual_layout.addWidget(self.manual_current_auto)
        self.manual_current_apps = QLineEdit()
        self.manual_current_apps.setPlaceholderText(
            "Current package IDs in exact on-screen order, e.g. org.smarttube.stable,com.netflix.ninja"
        )
        manual_layout.addWidget(self.manual_current_apps)
        manual_quick_row = QHBoxLayout()
        self.manual_quick_bluetooth = QCheckBox("Current: Bluetooth")
        self.manual_quick_sound = QCheckBox("Current: Sound")
        self.manual_quick_picture = QCheckBox("Current: Picture")
        for widget in (self.manual_quick_bluetooth, self.manual_quick_sound, self.manual_quick_picture):
            manual_quick_row.addWidget(widget)
        manual_layout.addLayout(manual_quick_row)
        self.manual_backup_group.setEnabled(False)
        custom_layout.addWidget(self.manual_backup_group)

        load_row = QHBoxLayout()
        load = QPushButton("Load current layout")
        load.clicked.connect(self.load_tv_layout)
        self.auto_apps = QCheckBox("Use tv-detox automatic app discovery")
        load_row.addWidget(load)
        load_row.addWidget(self.auto_apps)
        load_row.addStretch()
        custom_layout.addLayout(load_row)

        pick_row = QHBoxLayout()
        apps_box = QGroupBox("TV app tiles")
        apps_layout = QVBoxLayout(apps_box)
        self.apps_list = QListWidget()
        self.apps_list.setMinimumHeight(170)
        self.apps_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        apps_layout.addWidget(self.apps_list)
        order_row = QHBoxLayout()
        move_up = QPushButton("Move tile up ↑")
        move_up.clicked.connect(lambda: self._move_checked_tile(-1))
        move_down = QPushButton("Move tile down ↓")
        move_down.clicked.connect(lambda: self._move_checked_tile(1))
        order_row.addWidget(move_up)
        order_row.addWidget(move_down)
        apps_layout.addLayout(order_row)
        apps_hint = QLabel("Checked rows are used as tiles. Select a checked row and move it to change TV tile order.")
        apps_hint.setObjectName("muted")
        apps_hint.setWordWrap(True)
        apps_layout.addWidget(apps_hint)
        pick_row.addWidget(apps_box, 2)

        quick_box = QGroupBox("Top-row shortcuts")
        quick_layout = QVBoxLayout(quick_box)
        self.quick_bluetooth = QCheckBox("Bluetooth")
        self.quick_sound = QCheckBox("Sound")
        self.quick_picture = QCheckBox("Picture / display")
        for widget in (self.quick_bluetooth, self.quick_sound, self.quick_picture):
            quick_layout.addWidget(widget)
        quick_layout.addStretch(1)
        pick_row.addWidget(quick_box, 1)
        custom_layout.addLayout(pick_row)
        self.apply_layout_button = QPushButton("Apply tile / shortcut layout")
        self.apply_layout_button.setObjectName("primary")
        self.apply_layout_button.setEnabled(False)
        self.apply_layout_button.clicked.connect(self.apply_tv_layout)
        custom_layout.addWidget(self.apply_layout_button)
        layout.addWidget(custom)
        layout.addStretch(1)
        self.tabs.addTab(page, "Launcher & UI")

    def connect_device(self):
        self._async("Connect to Android TV", tv.connect)

    def scan_health(self):
        self._async("Read Android TV health", tv.health_check)

    def refresh_candidates(self):
        try:
            params = self._params()
        except Exception as exc:
            QMessageBox.warning(self, "Connection details", str(exc))
            return
        self.connection_status.setText("Working: read optional-package candidates…")
        self.run_job(
            lambda: tv.package_candidates(**params),
            done=self._populate_candidates,
            fail=lambda error: self._show_error("Read optional-package candidates", error),
            label="Read optional-package candidates",
        )

    def _populate_candidates(self, candidates):
        self._candidate_data = list(candidates or [])
        self.candidate_table.setRowCount(0)
        for row, candidate in enumerate(self._candidate_data):
            self.candidate_table.insertRow(row)
            values = (candidate["package"], candidate["state"], candidate["description"])
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.ItemDataRole.UserRole, candidate["package"])
                self.candidate_table.setItem(row, column, item)
        self.connection_status.setText(f"Loaded {len(self._candidate_data)} optional package candidate(s).")
        rendered = json.dumps(self._candidate_data, indent=2, ensure_ascii=False)
        self.output.setPlainText("ANDROID TV OPTIONAL-PACKAGE REVIEW\n" + rendered)
        self._show_detail(rendered)

    def _select_package(self):
        row = self.candidate_table.currentRow()
        if row < 0 or row >= len(self._candidate_data):
            QMessageBox.information(self, "Select a package", "Select one package row first.")
            return None
        return self._candidate_data[row]

    def change_selected_package(self, restore):
        candidate = self._select_package()
        if not candidate:
            return
        package = candidate["package"]
        state = candidate["state"]
        if restore:
            if state != "disabled":
                QMessageBox.information(self, "No change needed", f"{package} is not currently disabled.")
                return
            verb = "restore"
            detail = "This enables the package for user 0; it will not reinstall or download anything."
        else:
            if state != "enabled":
                QMessageBox.information(self, "No change possible", f"{package} is currently {state}; refresh before continuing.")
                return
            verb = "disable"
            detail = candidate["description"]
        answer = QMessageBox.question(
            self,
            f"Confirm {verb}: {package}",
            f"{verb.title()} {package}?\n\n{detail}\n\nThis changes only this one package. The inverse is recorded locally.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        action = tv.enable_package if restore else tv.disable_package
        label = f"{verb.title()} {package}"
        try:
            params = self._params()
        except Exception as exc:
            QMessageBox.warning(self, "Connection details", str(exc))
            return
        self.connection_status.setText(f"Working: {label}…")
        self.run_job(
            lambda: action(package, **params),
            done=lambda value: self._package_change_done(label, value),
            fail=lambda error: self._show_error(label, error),
            label=label,
        )

    def _package_change_done(self, label, value):
        self._show_result(label, value)
        self.refresh_candidates()

    def disable_animations(self):
        if QMessageBox.question(
            self, "Disable Android animations",
            "Set window, transition, and animator scales to 0?\n\nThe exact previous values will be saved for Undo.",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Disable Android animations", tv.set_animation_scales_zero)

    def turn_off_screensaver(self):
        if QMessageBox.question(
            self, "Disable screensaver",
            "Set secure screensaver_enabled to 0?\n\nThe exact previous value will be saved for Undo.",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Disable Android screensaver", tv.disable_screensaver)

    def trim_caches(self):
        if QMessageBox.question(
            self, "Trim Android caches",
            "Run pm trim-caches 512M?\n\nThis operation has no exact undo; app caches may rebuild and some apps may initially load more slowly.",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Trim Android package caches (no undo)", tv.run_cache_trim)

    def compile_apps(self):
        if QMessageBox.question(
            self, "Compile Android apps",
            "Run cmd package compile -m speed-profile -a?\n\nThis can take several minutes, firmware may reject it, and there is no exact inverse. Continue?",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Compile apps (no undo)", tv.compile_apps_speed_profile)

    def undo_last(self):
        if QMessageBox.question(
            self, "Undo latest recorded TV change",
            "Undo the newest not-yet-undone reversible change for this TV? Any newer no-inverse operations will remain untouched and be listed in the result.",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Undo latest Android TV change", tv.undo_last_change)

    def open_settings(self):
        self._async("Open Android Settings", tv.open_tv_settings)

    def install_selected_launcher(self):
        package = self.install_target.currentData()
        if package == tv.FIZXIX_HOME_PACKAGE:
            bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
            candidates = (
                bundle_root / "build_assets" / "FIZXIX-TV-Detox.apk",
                Path(__file__).resolve().parent.parent / "build_assets" / "FIZXIX-TV-Detox.apk",
                Path(__file__).resolve().parent.parent / "dist" / "FIZXIX-TV-Detox.apk",
            )
            apk_path = next((candidate for candidate in candidates if candidate.is_file() and candidate.stat().st_size > 25_000), None)
            if apk_path is None:
                QMessageBox.warning(
                    self,
                    "FIZXIX Home payload missing",
                    "This build does not contain the FIZXIX Home APK. Download the latest WindowsOptimizer-windows-x64 build from GitHub Actions.",
                )
                return
            try:
                params = self._params()
            except Exception as exc:
                QMessageBox.warning(self, "Connection details", str(exc))
                return
            answer = QMessageBox.question(
                self,
                "Install / update FIZXIX Home",
                "Install the bundled FIZXIX Home (com.fizxix.tvhome)?\\n\\n"
                "The APK ships with Windows Optimizer, so no separate file selection is needed. "
                "Google TV Home remains installed. If Android reports UPDATE_INCOMPATIBLE, stop; "
                "the signing key differs and no app will be uninstalled automatically.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
            self.connection_status.setText("Working: install / update FIZXIX Home…")
            self.run_job(
                lambda: tv.install_fizxix_home(str(apk_path), **params),
                done=lambda value: self._show_result("Install / update FIZXIX Home", value),
                fail=lambda error: self._show_error("Install / update FIZXIX Home", error),
                label="Install / update FIZXIX Home",
            )
            return

        if package == tv.TV_DETOX_PACKAGE:
            if QMessageBox.question(
                self,
                "Install / update Official TV Detox",
                "Download the official Ansub/tv-detox release over HTTPS and install it with ADB? "
                "The existing app will not be uninstalled.",
            ) == QMessageBox.StandardButton.Yes:
                self._async("Install / update Official TV Detox", tv.install_or_update_tv_detox)
            return

        QMessageBox.warning(self, "Unsupported launcher", "Select a supported launcher.")

    def set_selected_launcher_home(self):
        package = self.install_target.currentData()
        if package == tv.FIZXIX_HOME_PACKAGE:
            if QMessageBox.question(
                self,
                "Set FIZXIX Home as Home",
                "Make FIZXIX Home the active Home launcher?\n\n"
                "The current Home is recorded for Undo. Google TV Home remains installed and can be restored.",
            ) == QMessageBox.StandardButton.Yes:
                self._async("Set FIZXIX Home as Home", tv.set_fizxix_home)
        elif package == tv.TV_DETOX_PACKAGE:
            self.set_tvdetox_home()
        else:
            QMessageBox.warning(self, "Unsupported launcher", "Select a supported launcher.")

    def set_tvdetox_home(self):
        try:
            params = self._params()
            serial = tv.target_serial(params["tv_ip"], params["port"])
        except Exception as exc:
            QMessageBox.warning(self, "Connection details", str(exc))
            return
        if QMessageBox.question(
            self, "Set tv-detox as Home",
            "Make com.ansub.tvhome/.MainActivity the default Home?\n\nThe current Home is captured for Undo. No launcher or setup package will be disabled. If verification fails, the previous Home is restored when possible.\n\nEmergency launcher recovery command:\nadb -s " + serial + " shell pm enable com.google.android.apps.tv.launcherx",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Set tv-detox as Home", tv.set_tv_detox_home)

    def restore_stock_home(self):
        if QMessageBox.question(
            self, "Restore Google TV Home",
            "Enable com.google.android.apps.tv.launcherx if needed, resolve its Home component, and set it as Home?\n\nThe operation is verified and attempts to return to the current Home if it fails. It will not uninstall tv-detox or change the setup-wizard package.",
        ) == QMessageBox.StandardButton.Yes:
            self._async("Restore Google TV Home", tv.restore_google_tv_home)

    def _manual_backup_changed(self, checked):
        if hasattr(self, "manual_backup_group"):
            self.manual_backup_group.setEnabled(checked)
        if hasattr(self, "apply_layout_button"):
            self.apply_layout_button.setEnabled(
                self._layout_loaded and (self._layout_readable or checked)
            )

    def _manual_current_auto_changed(self, checked):
        self.manual_current_apps.setEnabled(not checked)

    def _selected_launcher_package(self):
        return self.launcher_target.currentData() or tv.TV_DETOX_PACKAGE

    def _selected_launcher_label(self):
        return "FIZXIX Home" if self._selected_launcher_package() == tv.FIZXIX_HOME_PACKAGE else "TV Detox"

    def _launcher_target_changed(self, *_args):
        self._layout_loaded = False
        self._layout_readable = False
        if hasattr(self, "apply_layout_button"):
            self.apply_layout_button.setEnabled(False)
        if hasattr(self, "connection_status"):
            self.connection_status.setText("Launcher selection changed; load its current layout before editing.")

    def load_tv_layout(self):
        try:
            params = self._params()
        except Exception as exc:
            QMessageBox.warning(self, "Connection details", str(exc))
            return
        launcher_package = self._selected_launcher_package()
        launcher_label = self._selected_launcher_label()
        self.connection_status.setText(f"Working: read {launcher_label} layout…")
        def task():
            packages = tv.tv_launchable_apps(**params)
            try:
                prefs = tv.tv_detox_layout(**params, launcher_package=launcher_package)
                return {
                    "preferences": prefs,
                    "packages": packages,
                    "layout_error": None,
                    "launcher_package": launcher_package,
                }
            except RuntimeError as exc:
                message = str(exc)
                if (
                    "Exact tv-detox layout backup is unavailable" in message
                    or "Could not parse tv-detox's saved layout" in message
                ):
                    return {
                        "preferences": None,
                        "packages": packages,
                        "layout_error": message,
                        "launcher_package": launcher_package,
                    }
                raise
        self.run_job(
            task,
            done=self._populate_tv_layout,
            fail=lambda error: self._show_error(f"Read {launcher_label} layout", error),
            label=f"Read {launcher_label} layout",
        )

    def _populate_tv_layout(self, result):
        prefs = result["preferences"]
        packages = result["packages"]
        layout_error = result.get("layout_error")
        self._layout_launcher_package = result.get("launcher_package", tv.TV_DETOX_PACKAGE)
        if self._layout_launcher_package != self._selected_launcher_package():
            self._layout_loaded = False
            self.apply_layout_button.setEnabled(False)
            self.connection_status.setText("Launcher selection changed during the read; load the selected layout again.")
            return
        self._layout_readable = prefs is not None

        saved_apps = prefs.get("apps") if prefs else None
        saved_quick = (prefs.get("quick") or "").replace(" ", "").split(",") if prefs and prefs.get("quick") else []
        if saved_apps:
            saved_app_order = [value.strip() for value in saved_apps.split(",") if value.strip()]
            saved_app_set = set(saved_app_order)
            # Keep the current custom tile order on load. Sorting the selected set
            # alphabetically would silently change the user's launcher layout on Apply.
            ordered_packages = saved_app_order + sorted(set(packages) - saved_app_set, key=str.casefold)
        else:
            saved_app_order = []
            saved_app_set = set()
            ordered_packages = sorted(set(packages), key=str.casefold)

        self.apps_list.clear()
        for package in ordered_packages:
            item = QListWidgetItem(package)
            item.setData(Qt.ItemDataRole.UserRole, package)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            if saved_apps and package in saved_app_set:
                item.setCheckState(Qt.CheckState.Checked)
            else:
                item.setCheckState(Qt.CheckState.Unchecked)
            if package not in packages:
                item.setText(f"{package}  (not found by current launcher query)")
            self.apps_list.addItem(item)

        if self._layout_readable:
            self.auto_apps.setChecked(not bool(saved_apps))
            self.quick_bluetooth.setChecked("bluetooth" in saved_quick)
            self.quick_sound.setChecked("sound" in saved_quick)
            self.quick_picture.setChecked("picture" in saved_quick)
            self.manual_current_auto.setChecked(not bool(saved_apps))
            self.manual_current_apps.setText(saved_apps or "")
            self.manual_quick_bluetooth.setChecked("bluetooth" in saved_quick)
            self.manual_quick_sound.setChecked("sound" in saved_quick)
            self.manual_quick_picture.setChecked("picture" in saved_quick)
            self.manual_backup_toggle.setChecked(False)
            self.manual_backup_toggle.setEnabled(False)
            self.manual_backup_group.setEnabled(False)
            self.connection_status.setText(
                f"Loaded {len(packages)} launchable app package(s); previous layout is readable and will be backed up automatically."
            )
            report = f"CURRENT {self._selected_launcher_label().upper()} LAYOUT\n" + json.dumps(prefs, indent=2)
        else:
            # Some official release builds are not debuggable, so Android's run-as
            # cannot read private SharedPreferences. Offer a manual, user-attested
            # rollback snapshot instead of making UI editing impossible or guessing.
            self.auto_apps.setChecked(False)
            self.quick_bluetooth.setChecked(False)
            self.quick_sound.setChecked(False)
            self.quick_picture.setChecked(False)
            self.manual_current_auto.setChecked(False)
            self.manual_current_apps.clear()
            self.manual_quick_bluetooth.setChecked(False)
            self.manual_quick_sound.setChecked(False)
            self.manual_quick_picture.setChecked(False)
            self.manual_backup_toggle.setChecked(False)
            self.manual_backup_toggle.setEnabled(True)
            self.manual_backup_group.setEnabled(False)
            self.connection_status.setText(
                f"Loaded {len(packages)} app candidate(s); current saved layout is not readable. Manual backup is required before Apply."
            )
            report = (
                "TV-DETOX SAVED LAYOUT NOT READABLE\n"
                + (layout_error or "The installed APK did not expose its saved preferences.")
                + "\n\nThe available TV app packages are listed below. To enable Windows-side tile editing, "
                "select the manual snapshot option and enter the CURRENT app tile package IDs in on-screen order "
                "(or confirm current automatic discovery) and currently enabled tv-detox shortcuts. "
                "Do not guess: Undo uses the values you enter.\n\n"
                + "\n".join(packages)
            )
        self._layout_loaded = True
        self.apply_layout_button.setEnabled(self._layout_readable)
        self.output.setPlainText(report + f"\n\nLaunchable package count: {len(packages)}")

    def _move_checked_tile(self, direction):
        selected = self.apps_list.currentItem()
        if selected is None or selected.checkState() != Qt.CheckState.Checked:
            QMessageBox.information(self, "Select a checked tile", "Select a checked app row first, then use Move tile up/down.")
            return
        items = [self.apps_list.takeItem(0) for _ in range(self.apps_list.count())]
        checked = [item for item in items if item.checkState() == Qt.CheckState.Checked]
        unchecked = [item for item in items if item.checkState() != Qt.CheckState.Checked]
        current = checked.index(selected)
        target = current + direction
        if target < 0 or target >= len(checked):
            ordered = checked + unchecked
            for item in ordered:
                self.apps_list.addItem(item)
            self.apps_list.setCurrentItem(selected)
            return
        checked[current], checked[target] = checked[target], checked[current]
        for item in checked + unchecked:
            self.apps_list.addItem(item)
        self.apps_list.setCurrentItem(selected)

    def apply_tv_layout(self):
        if not self._layout_loaded:
            QMessageBox.information(self, "Load first", "Load the selected launcher's current layout first so the current state can be backed up.")
            return
        launcher_package = self._selected_launcher_package()
        if getattr(self, "_layout_launcher_package", None) != launcher_package:
            QMessageBox.information(self, "Reload layout", "The selected launcher differs from the loaded snapshot. Load its current layout again.")
            return
        manual_before = None
        if not self._layout_readable:
            if not self.manual_backup_toggle.isChecked():
                QMessageBox.warning(
                    self, "Backup required",
                    "This release of tv-detox does not expose its saved preferences. Enable the manual snapshot "
                    "and enter the verified current app order/shortcuts before applying any UI change.",
                )
                return
            if self.manual_current_auto.isChecked():
                previous_apps = None
            else:
                current_text = self.manual_current_apps.text().strip()
                if not current_text:
                    QMessageBox.warning(
                        self, "Current layout required",
                        "Enter the current app package IDs in exact on-screen order, or check that the current app row uses automatic discovery.",
                    )
                    return
                previous_apps = [part.strip() for part in current_text.split(",") if part.strip()]
            previous_quick = []
            if self.manual_quick_bluetooth.isChecked():
                previous_quick.append("bluetooth")
            if self.manual_quick_sound.isChecked():
                previous_quick.append("sound")
            if self.manual_quick_picture.isChecked():
                previous_quick.append("picture")
            manual_before = {"apps": previous_apps, "quick": previous_quick}

        apps = [] if self.auto_apps.isChecked() else [
            item.data(Qt.ItemDataRole.UserRole)
            for index in range(self.apps_list.count())
            for item in [self.apps_list.item(index)]
            if item.checkState() == Qt.CheckState.Checked and item.data(Qt.ItemDataRole.UserRole)
        ]
        quick = []
        if self.quick_bluetooth.isChecked():
            quick.append("bluetooth")
        if self.quick_sound.isChecked():
            quick.append("sound")
        if self.quick_picture.isChecked():
            quick.append("picture")
        if not self.auto_apps.isChecked() and not apps:
            QMessageBox.warning(self, "No app tiles selected", "Select at least one TV app tile or enable automatic app discovery.")
            return

        if manual_before is None:
            backup_summary = "Prior preferences will be read directly from tv-detox and saved for Undo."
        else:
            backup_summary = (
                "Manual rollback snapshot (you confirm these match the current TV):\n"
                + ("Apps: automatic discovery" if manual_before["apps"] is None else "Apps in order: " + ", ".join(manual_before["apps"]))
                + "\nShortcuts: " + (", ".join(manual_before["quick"]) if manual_before["quick"] else "none")
            )
        answer = QMessageBox.question(
            self, "Apply tv-detox UI layout",
            "Apply this app tile and shortcut configuration?\n\n"
            + ("App tiles: automatic discovery" if self.auto_apps.isChecked() else "App tiles: " + ", ".join(apps))
            + "\nShortcuts: " + (", ".join(quick) if quick else "none")
            + "\n\n" + backup_summary
            + "\n\nThe change will be journaled and can be undone using this snapshot.",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._layout_loaded = False
        self.apply_layout_button.setEnabled(False)
        try:
            params = self._params()
        except Exception as exc:
            QMessageBox.warning(self, "Connection details", str(exc))
            self._layout_loaded = True
            self.apply_layout_button.setEnabled(self._layout_readable or self.manual_backup_toggle.isChecked())
            return
        self.connection_status.setText("Working: apply tv-detox UI layout…")
        self.run_job(
            lambda: tv.configure_tv_detox(
                apps=apps,
                quick_shortcuts=quick,
                manual_before=manual_before,
                launcher_package=launcher_package,
                **params,
            ),
            done=lambda value: self._layout_apply_done(value),
            fail=lambda error: self._layout_apply_failed(error),
            label="Apply tv-detox UI layout",
        )

    def _layout_apply_done(self, value):
        self._show_result("Apply tv-detox UI layout", value)
        self.load_tv_layout()

    def _layout_apply_failed(self, error):
        self._show_error("Apply tv-detox UI layout", error)
        self._layout_loaded = True
        self.apply_layout_button.setEnabled(self._layout_readable or self.manual_backup_toggle.isChecked())
