from PySide6.QtCore import Qt
from PySide6.QtWidgets import QCheckBox,QComboBox,QGridLayout,QGroupBox,QHBoxLayout,QLabel,QLineEdit,QMessageBox,QPushButton,QScrollArea,QVBoxLayout,QWidget
from core.system_info import is_admin
from modules.software import CATALOG,install_selected

class SoftwarePanel(QWidget):
    def __init__(self, output, run_job):
        super().__init__(); self.output=output; self.run_job=run_job; self.selected_ids=set(); self._build()

    def _build(self):
        root=QVBoxLayout(self)
        intro=QLabel("<b>Install Windows 11 Apps</b><br>Choose applications from the curated WinGet catalog, review the selection, then install them together. Exact package IDs are used instead of arbitrary search results.")
        intro.setWordWrap(True); root.addWidget(intro)
        controls=QHBoxLayout()
        self.search=QLineEdit(); self.search.setPlaceholderText("Search applications..."); self.search.textChanged.connect(self._render); controls.addWidget(self.search)
        self.category=QComboBox(); self.category.addItem("All categories"); self.category.addItems(sorted({app.category for app in CATALOG})); self.category.currentTextChanged.connect(self._render); controls.addWidget(self.category)
        self.foss=QCheckBox("FOSS only"); self.foss.toggled.connect(self._render); controls.addWidget(self.foss); root.addLayout(controls)
        actions=QHBoxLayout()
        for text,fn in (("Screenshot Essentials",self.select_screenshot_essentials),("Select Visible",self.select_visible),("Clear",self.clear),("Install Selected",self.install)):
            b=QPushButton(text); b.clicked.connect(fn); actions.addWidget(b)
        actions.addStretch(); self.count=QLabel(); actions.addWidget(self.count); root.addLayout(actions)
        self.scroll=QScrollArea(); self.scroll.setWidgetResizable(True); self.container=QWidget(); self.grid=QGridLayout(self.container); self.grid.setAlignment(Qt.AlignmentFlag.AlignTop); self.scroll.setWidget(self.container); root.addWidget(self.scroll)
        note=QLabel("WinGet handles the actual installer and package agreements. Store-backed packages are marked. No third-party installer downloads are bundled into WindowsOptimizer."); note.setWordWrap(True); root.addWidget(note); self._render()

    def _visible(self):
        query=self.search.text().strip().lower(); category=self.category.currentText(); foss_only=self.foss.isChecked()
        return [app for app in CATALOG if (not query or query in app.name.lower() or query in app.id.lower()) and (category=="All categories" or app.category==category) and (not foss_only or app.foss)]

    def _toggle(self, package_id, state):
        if state:
            self.selected_ids.add(package_id)
        else:
            self.selected_ids.discard(package_id)
        self._update_count()

    def _render(self):
        while self.grid.count():
            item=self.grid.takeAt(0); widget=item.widget()
            if widget: widget.deleteLater()
        visible=self._visible()
        for index,app in enumerate(visible):
            box=QGroupBox(); layout=QVBoxLayout(box)
            check=QCheckBox(app.name); check.setProperty("package_id",app.id); check.setChecked(app.id in self.selected_ids)
            check.stateChanged.connect(lambda state, package_id=app.id: self._toggle(package_id,state))
            layout.addWidget(check)
            details=QLabel(f"{app.description}<br><small>{app.category} • {app.id}{' • Microsoft Store' if app.source=='msstore' else ''}{' • FOSS' if app.foss else ''}</small>"); details.setWordWrap(True); layout.addWidget(details)
            row,col=divmod(index,2); self.grid.addWidget(box,row,col)
        self._update_count(len(visible))

    def _update_count(self, shown=None):
        if shown is None: shown=len(self._visible())
        self.count.setText(f"{len(self.selected_ids)} selected • {shown} shown")

    def select_visible(self):
        self.selected_ids.update(app.id for app in self._visible()); self._render()

    def select_screenshot_essentials(self):
        ids={"Google.Chrome","Valve.Steam","9WZDNCRFJ3TJ","qBittorrent.qBittorrent","Spotify.Spotify","Microsoft.PowerShell","Microsoft.OneNote"}
        self.selected_ids.update(ids); self._render()

    def clear(self):
        self.selected_ids.clear(); self._render()

    def install(self):
        selected=[app.id for app in CATALOG if app.id in self.selected_ids]
        if not selected: return QMessageBox.information(self,"Nothing selected","Select at least one application.")
        if not is_admin(): return QMessageBox.warning(self,"Administrator required","Run Windows Optimizer as Administrator to install applications.")
        names=[app.name for app in CATALOG if app.id in selected]
        answer=QMessageBox.question(self,"Install selected applications",f"Install {len(names)} application(s)?\n\n"+"\n".join(f"• {name}" for name in names))
        if answer != QMessageBox.StandardButton.Yes: return
        self.run_job(install_selected,selected,done=self._installed,fail=self._failed)

    def _installed(self,value):
        self.output.setPlainText(value); self._render()

    def _failed(self,error):
        self.output.setPlainText(f"Application installation failed:\n{error}")

    def focus_search(self):
        self.search.setFocus()
