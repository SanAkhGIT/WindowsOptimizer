from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from modules.browser_extensions import (
    catalog,
    install,
    installation_status,
    manifest,
    open_edge_extensions,
    open_install_folder,
    remove,
)


class BrowserExtensionsPanel(QWidget):
    def __init__(self, output=None):
        super().__init__()
        self.output = output
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)

        intro = QLabel(
            "Install and manage bundled Microsoft Edge extensions. "
            "Unpacked extensions are kept in an app-managed folder and must be "
            "loaded from edge://extensions/ with Developer mode enabled."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.extensions = QListWidget()
        for extension in catalog():
            item = QListWidgetItem(
                f"{extension.name}  •  v{extension.version}  •  {extension.browser}"
            )
            item.setData(32, extension.id)
            self.extensions.addItem(item)
        self.extensions.setCurrentRow(0)
        self.extensions.currentItemChanged.connect(self._refresh_status)
        layout.addWidget(self.extensions)

        details = QGroupBox("Selected extension")
        details_layout = QVBoxLayout(details)
        self.description = QLabel()
        self.description.setWordWrap(True)
        details_layout.addWidget(self.description)
        self.status = QLabel()
        self.status.setWordWrap(True)
        details_layout.addWidget(self.status)
        layout.addWidget(details)

        actions = QHBoxLayout()
        self.install_button = QPushButton("Prepare / Install")
        self.install_button.clicked.connect(self._install)
        actions.addWidget(self.install_button)

        self.edge_button = QPushButton("Open Edge Extensions")
        self.edge_button.clicked.connect(self._open_edge)
        actions.addWidget(self.edge_button)

        self.folder_button = QPushButton("Open Install Folder")
        self.folder_button.clicked.connect(self._open_folder)
        actions.addWidget(self.folder_button)

        self.remove_button = QPushButton("Remove Local Copy")
        self.remove_button.clicked.connect(self._remove)
        actions.addWidget(self.remove_button)

        actions.addStretch()
        layout.addLayout(actions)

        steps = QLabel(
            "<b>After Prepare / Install:</b> open Edge Extensions → enable "
            "<b>Developer mode</b> → choose <b>Load unpacked</b> → select the "
            "path shown above. Edge controls the final extension registration."
        )
        steps.setWordWrap(True)
        layout.addWidget(steps)

        self._refresh_status()

    def _selected_id(self):
        item = self.extensions.currentItem()
        return item.data(32) if item else None

    def _refresh_status(self, *_):
        extension_id = self._selected_id()
        extension = next((e for e in catalog() if e.id == extension_id), None)
        if not extension:
            return
        details = manifest(extension_id)
        permissions = ", ".join(details.get("permissions", [])) or "None"
        hosts = ", ".join(details.get("host_permissions", [])) or "None"
        self.description.setText(
            f"{extension.description}<br><br>"
            f"<b>Source:</b> {extension.source_url}<br>"
            f"<b>Permissions:</b> {permissions}<br>"
            f"<b>Host access:</b> {hosts}"
        )
        state = installation_status(extension_id)
        if state["installed"]:
            self.status.setText(
                f"Status: Prepared • Version {state['version']}<br>"
                f"Path: {state['path']}"
            )
            self.folder_button.setEnabled(True)
            self.remove_button.setEnabled(True)
        else:
            self.status.setText(f"Status: Not prepared<br>Path: {state['path']}")
            self.folder_button.setEnabled(False)
            self.remove_button.setEnabled(False)

    def _install(self):
        extension_id = self._selected_id()
        if not extension_id:
            return
        try:
            path = install(extension_id)
            try:
                open_edge_extensions()
            except Exception:
                pass
            self._refresh_status()
            if self.output:
                self.output.setPlainText(
                    f"EDGE EXTENSION PREPARED\n{path}\n\n"
                    "Edge extension management has been opened. Enable "
                    "Developer mode, then choose Load unpacked and select this "
                    "folder."
                )
            QMessageBox.information(
                self,
                "Extension prepared",
                "The extension files are ready.\n\n"
                f"{path}\n\n"
                "Edge extension management has been opened. Enable Developer "
                "mode, choose Load unpacked, and select this folder.",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Extension install failed", str(exc))

    def _open_edge(self):
        try:
            message = open_edge_extensions()
            if self.output:
                self.output.setPlainText(message)
        except Exception as exc:
            QMessageBox.warning(self, "Microsoft Edge", str(exc))

    def _open_folder(self):
        extension_id = self._selected_id()
        if not extension_id:
            return
        try:
            open_install_folder(extension_id)
        except Exception as exc:
            QMessageBox.warning(self, "Extension folder", str(exc))

    def _remove(self):
        extension_id = self._selected_id()
        if not extension_id:
            return
        if QMessageBox.question(
            self,
            "Remove local extension files",
            "Remove the Windows Optimizer managed copy of this extension?\n\n"
            "This does not remove an Edge extension entry that you already "
            "loaded; remove that entry separately from edge://extensions/.",
        ) != QMessageBox.StandardButton.Yes:
            return
        try:
            message = remove(extension_id)
            self._refresh_status()
            if self.output:
                self.output.setPlainText(message)
        except Exception as exc:
            QMessageBox.critical(self, "Remove failed", str(exc))
