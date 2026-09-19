from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.system_info import is_admin
from modules.appx import AppxPackage, inventory, register_existing_manifest, remove_packages


class AppxPanel(QWidget):
    def __init__(self, output, run_job, open_system_debloat=None):
        super().__init__()
        self.output = output
        self.run_job = run_job
        self.open_system_debloat = open_system_debloat
        self.packages = []
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        title = QLabel("AppX Debloat")
        title.setObjectName("section")
        layout.addWidget(title)

        description = QLabel(
            "Review installed Windows AppX packages before removal. "
            "Only exact selected package names are passed to PowerShell; "
            "framework and protected packages are blocked from removal."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(description)

        system_card = QHBoxLayout()
        system_label = QLabel(
            "System debloat: reversible privacy/UI policies such as Widgets and "
            "consumer-content controls are managed separately from AppX removal."
        )
        system_label.setObjectName("muted")
        system_label.setWordWrap(True)
        system_card.addWidget(system_label, 1)
        if self.open_system_debloat:
            system_button = QPushButton("System debloat tweaks")
            system_button.setToolTip("Open the reversible system debloat controls in Optimize.")
            system_button.clicked.connect(self.open_system_debloat)
            system_card.addWidget(system_button)
        layout.addLayout(system_card)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search package name or publisher…")
        self.search.textChanged.connect(self._render)
        controls.addWidget(self.search, 1)

        self.all_users = QCheckBox("Inventory all users")
        self.all_users.setToolTip("Requires Administrator and may include packages from other profiles.")
        controls.addWidget(self.all_users)

        self.recommended_only = QCheckBox("Recommended candidates only")
        self.recommended_only.setChecked(True)
        self.recommended_only.toggled.connect(self._render)
        controls.addWidget(self.recommended_only)

        self.scan_button = QPushButton("Scan")
        self.scan_button.clicked.connect(self.scan)
        controls.addWidget(self.scan_button)
        layout.addLayout(controls)

        actions = QHBoxLayout()
        self.select_visible = QPushButton("Select visible")
        self.select_visible.clicked.connect(self._select_visible)
        actions.addWidget(self.select_visible)

        clear = QPushButton("Clear")
        clear.clicked.connect(self._clear_selection)
        actions.addWidget(clear)

        self.remove = QPushButton("Remove selected")
        self.remove.setObjectName("primary")
        self.remove.clicked.connect(self.remove_selected)
        actions.addWidget(self.remove)

        self.register = QPushButton("Register existing files")
        self.register.clicked.connect(self.register_selected)
        actions.addWidget(self.register)

        actions.addStretch()
        layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ("Package", "Version", "Publisher", "Status", "Scope", "Install location")
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        self.summary = QLabel("No inventory loaded. Click Scan to inspect installed AppX packages.")
        self.summary.setObjectName("muted")
        layout.addWidget(self.summary)

    def scan(self):
        if self.all_users.isChecked() and not is_admin():
            QMessageBox.warning(
                self,
                "Administrator required",
                "Run Windows Optimizer as Administrator to inventory all user profiles.",
            )
            return
        self.scan_button.setEnabled(False)
        self.scan_button.setText("Scanning…")
        self.summary.setText(
            "Scanning installed AppX packages… this may take a few seconds."
        )

        def failed(error):
            self.scan_button.setEnabled(True)
            self.scan_button.setText("Scan")
            self.summary.setText("Scan failed. See Activity for details.")
            self.output.setPlainText(f"AppX scan failed:\n{error}")

        def loaded(packages):
            self.scan_button.setEnabled(True)
            self.scan_button.setText("Scan")
            self._loaded(packages)

        self.run_job(
            inventory,
            self.all_users.isChecked(),
            done=loaded,
            fail=failed,
            label="Scanning AppX packages",
        )

    def _loaded(self, packages):
        self.packages = packages
        self._render()
        removable = sum(package.removable for package in packages)
        recommended = sum(package.recommended for package in packages)
        self.output.setPlainText(
            f"APPX INVENTORY\n{len(packages)} package(s) found • "
            f"{removable} removable • {recommended} recommended candidates"
        )

    def _filtered(self):
        query = self.search.text().strip().lower()
        result = []
        for package in self.packages:
            if self.recommended_only.isChecked() and not package.recommended:
                continue
            haystack = " ".join(
                (package.name, package.publisher, package.version)
            ).lower()
            if query and query not in haystack:
                continue
            result.append(package)
        return result

    def _render(self):
        self.table.setRowCount(0)
        for package in self._filtered():
            row = self.table.rowCount()
            self.table.insertRow(row)
            item = QTableWidgetItem(package.name)
            item.setData(Qt.ItemDataRole.UserRole, package.package_full_name)
            self.table.setItem(row, 0, item)
            self.table.setItem(row, 1, QTableWidgetItem(package.version))
            self.table.setItem(row, 2, QTableWidgetItem(package.publisher))
            status = "Recommended" if package.recommended else (
                "Removable" if package.removable else "Protected"
            )
            self.table.setItem(row, 3, QTableWidgetItem(status))
            self.table.setItem(row, 4, QTableWidgetItem(package.scope))
            self.table.setItem(row, 5, QTableWidgetItem(package.install_location))

        self.summary.setText(
            f"{len(self._filtered())} shown • {len(self.packages)} total inventory"
        )

    def _visible_rows(self):
        return range(self.table.rowCount())

    def _select_visible(self):
        self.table.clearSelection()
        for row in self._visible_rows():
            self.table.selectRow(row)

    def _clear_selection(self):
        self.table.clearSelection()

    def _selected_packages(self):
        selected = []
        seen = set()
        for row in self.table.selectionModel().selectedRows():
            package = self.table.item(row.row(), 0).data(Qt.ItemDataRole.UserRole)
            if package and package not in seen:
                selected.append(package)
                seen.add(package)
        return selected

    def _selected_models(self):
        selected_names = set(self._selected_packages())
        return [
            package
            for package in self.packages
            if package.package_full_name in selected_names
        ]

    def remove_selected(self):
        models = self._selected_models()
        if not models:
            QMessageBox.information(self, "Nothing selected", "Select at least one AppX package.")
            return

        blocked = [package.name for package in models if not package.removable]
        if blocked:
            QMessageBox.warning(
                self,
                "Protected package selected",
                "These packages cannot be removed by Windows Optimizer:\n\n"
                + "\n".join(blocked),
            )
            return

        all_users = self.all_users.isChecked()
        if all_users and not is_admin():
            QMessageBox.warning(self, "Administrator required", "Run as Administrator for all-user removal.")
            return

        scope = "all user profiles" if all_users else "the current user"
        names = "\n".join(package.name for package in models[:12])
        suffix = "\n…" if len(models) > 12 else ""
        if QMessageBox.question(
            self,
            "Confirm AppX removal",
            f"Remove {len(models)} package(s) from {scope}?\n\n{names}{suffix}\n\n"
            "This operation targets exact package full names. Microsoft notes that AppX removal can be irreversible.",
        ) != QMessageBox.StandardButton.Yes:
            return

        self.run_job(
            remove_packages,
            [package.package_full_name for package in models],
            all_users,
            done=lambda result: self._removed(result),
            fail=lambda error: self.output.setPlainText(f"AppX removal failed:\n{error}"),
        )

    def _removed(self, result):
        self.output.setPlainText(result)
        self.scan()

    def register_selected(self):
        models = self._selected_models()
        if not models:
            QMessageBox.information(self, "Nothing selected", "Select a package with an existing installation location.")
            return

        eligible = [package for package in models if package.install_location]
        if not eligible:
            QMessageBox.information(
                self,
                "No package files",
                "The selected packages do not expose an installation location that can be registered.",
            )
            return

        def register_all():
            messages = []
            for package in eligible:
                try:
                    messages.append(f"{package.name}: {register_existing_manifest(package.install_location)}")
                except Exception as exc:
                    messages.append(f"{package.name}: FAILED — {exc}")
            return "\n".join(messages)

        self.run_job(register_all, done=lambda result: self.output.setPlainText(result), fail=lambda error: self.output.setPlainText(str(error)))
