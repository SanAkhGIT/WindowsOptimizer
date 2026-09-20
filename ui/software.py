from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QGridLayout, QHBoxLayout, QLabel, QLineEdit,
    QMessageBox, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from modules.software import CATALOG, install_selected


class SoftwarePanel(QWidget):
    """Curated WinGet catalog with responsive cards and explicit batch selection."""

    def __init__(self, output, run_job):
        super().__init__()
        self.output = output
        self.run_job = run_job
        self.selected_ids = set()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        title = QLabel("App Library")
        title.setObjectName("section")
        root.addWidget(title)

        intro = QLabel(
            "Install trusted catalog entries through WinGet. Search, filter, "
            "select a batch, review it, then install."
        )
        intro.setObjectName("muted")
        intro.setWordWrap(True)
        root.addWidget(intro)

        filters = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search apps or package IDs…")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self._render)
        filters.addWidget(self.search, 1)

        self.category = QComboBox()
        self.category.addItem("All categories")
        self.category.addItems(sorted({app.category for app in CATALOG}))
        self.category.currentTextChanged.connect(self._render)
        filters.addWidget(self.category)

        self.foss = QCheckBox("FOSS")
        self.foss.setToolTip("Show only free/open-source catalog entries.")
        self.foss.toggled.connect(self._render)
        filters.addWidget(self.foss)
        root.addLayout(filters)

        actions = QHBoxLayout()
        for text, fn in (
            ("Screenshot essentials", self.select_screenshot_essentials),
            ("Select visible", self.select_visible),
            ("Clear selection", self.clear),
        ):
            button = QPushButton(text)
            button.clicked.connect(fn)
            actions.addWidget(button)

        actions.addStretch()
        self.count = QLabel()
        self.count.setObjectName("pageStatus")
        actions.addWidget(self.count)

        self.install_button = QPushButton("Install selected")
        self.install_button.setObjectName("primary")
        self.install_button.clicked.connect(self.install)
        actions.addWidget(self.install_button)
        root.addLayout(actions)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        self.container = QWidget()
        self.grid = QGridLayout(self.container)
        self.grid.setContentsMargins(2, 2, 2, 12)
        self.grid.setHorizontalSpacing(12)
        self.grid.setVerticalSpacing(12)
        self.grid.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.container)
        root.addWidget(self.scroll, 1)

        note = QLabel(
            "WinGet handles installers and package agreements. WindowsOptimizer "
            "does not bundle third-party installers."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        root.addWidget(note)
        self._render()

    def _visible(self):
        query = self.search.text().strip().lower()
        category = self.category.currentText()
        foss_only = self.foss.isChecked()
        return [
            app for app in CATALOG
            if (
                not query
                or query in app.name.lower()
                or query in app.id.lower()
                or query in app.description.lower()
            )
            and (category == "All categories" or app.category == category)
            and (not foss_only or app.foss)
        ]

    def _toggle(self, package_id, checked):
        if checked:
            self.selected_ids.add(package_id)
        else:
            self.selected_ids.discard(package_id)
        self._update_count()

    def _render(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        visible = self._visible()
        for index, app in enumerate(visible):
            card = QWidget()
            card.setObjectName("card")
            layout = QVBoxLayout(card)
            layout.setContentsMargins(13, 11, 13, 11)
            layout.setSpacing(7)

            check = QCheckBox(app.name)
            check.setChecked(app.id in self.selected_ids)
            check.stateChanged.connect(
                lambda state, package_id=app.id:
                    self._toggle(package_id, bool(state))
            )
            layout.addWidget(check)

            details = QLabel(app.description)
            details.setObjectName("muted")
            details.setWordWrap(True)
            layout.addWidget(details)

            tags = " • ".join(
                filter(
                    None,
                    (
                        app.category,
                        "Microsoft Store" if app.source == "msstore" else "WinGet",
                        "FOSS" if app.foss else None,
                    ),
                )
            )
            meta = QLabel(tags)
            meta.setObjectName("cardMeta")
            meta.setToolTip(app.id)
            layout.addWidget(meta)

            row, col = divmod(index, 2)
            self.grid.addWidget(card, row, col)

        if not visible:
            empty = QLabel("No apps match the current filters.")
            empty.setObjectName("muted")
            empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid.addWidget(empty, 0, 0, 1, 2)

        self._update_count(len(visible))

    def _update_count(self, shown=None):
        if shown is None:
            shown = len(self._visible())
        selected_visible = sum(1 for app in self._visible() if app.id in self.selected_ids)
        self.count.setText(
            f"{len(self.selected_ids)} selected • {selected_visible} visible • {shown} shown"
        )
        self.install_button.setEnabled(bool(self.selected_ids))

    def select_visible(self):
        self.selected_ids.update(app.id for app in self._visible())
        self._render()

    def select_screenshot_essentials(self):
        ids = {
            "Google.Chrome", "Valve.Steam", "9WZDNCRFJ3TJ",
            "qBittorrent.qBittorrent", "Spotify.Spotify",
            "Microsoft.PowerShell", "ElementLabs.LMStudio",
            "Stremio.Stremio", "AppWork.JDownloader", "9N9WCLWDQS5J",
        }
        self.selected_ids.update(
            app.id for app in CATALOG if app.id in ids
        )
        self._render()

    def clear(self):
        self.selected_ids.clear()
        self._render()

    def install(self):
        selected = [app.id for app in CATALOG if app.id in self.selected_ids]
        if not selected:
            QMessageBox.information(
                self, "Nothing selected", "Select at least one application."
            )
            return

        names = [app.name for app in CATALOG if app.id in selected]
        preview = "\n".join(f"• {name}" for name in names[:20])
        if len(names) > 20:
            preview += f"\n• …and {len(names) - 20} more"

        answer = QMessageBox.question(
            self,
            "Install selected applications",
            f"Install {len(names)} application(s)?\n\n{preview}",
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        self.run_job(
            install_selected,
            selected,
            done=self._installed,
            fail=self._failed,
            label=f"Installing {len(selected)} application(s)",
        )

    def _installed(self, value):
        self.output.setPlainText(str(value))
        self.selected_ids.clear()
        self._render()

    def _failed(self, error):
        self.output.setPlainText(f"Application installation failed:\n{error}")

    def focus_search(self):
        self.search.setFocus()
