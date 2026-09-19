from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QTextEdit,QCheckBox,QMessageBox,QTabWidget,QGroupBox,QScrollArea,QListWidget,QListWidgetItem
from core.system_info import get_system_info,is_admin
from core.backup import BackupManager
from core.executor import Executor
from core.restore import create_restore_point
from modules.catalog import all_tweaks
from modules.software import installed_apps,CATALOG,install,upgrade_all
from modules.updates import scan as scan_updates
from modules.repair import explorer,sfc,dism
class MainWindow(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle("Windows Optimizer"); self.resize(1180,800); self.backup=BackupManager(); self.executor=Executor(); self._build_ui(); self.refresh()
 def _build_ui(self):
  c=QWidget(); self.setCentralWidget(c); root=QVBoxLayout(c); h=QHBoxLayout(); t=QLabel("Windows Optimizer"); t.setStyleSheet("font-size:26px;font-weight:700;"); h.addWidget(t); h.addStretch(); self.admin=QLabel(); h.addWidget(self.admin); root.addLayout(h); self.system=QLabel(); self.system.setWordWrap(True); root.addWidget(self.system)
  bar=QHBoxLayout()
  for text,fn in [("Scan",self.refresh),("Backup",self.create_backup),("Restore Point",self.restore_point),("Apply Selected",self.apply_selected)]: b=QPushButton(text); b.clicked.connect(fn); bar.addWidget(b)
  root.addLayout(bar); self.tabs=QTabWidget(); root.addWidget(self.tabs,1); self.output=QTextEdit(); self.output.setReadOnly(True); self.output.setMaximumHeight(160); root.addWidget(self.output)
  self._build_tweaks_tab(); self._build_software_tab(); self._build_updates_tab(); self._build_repairs_tab()
 def _build_tweaks_tab(self):
  self.tweak_tab=QWidget(); lay=QVBoxLayout(self.tweak_tab); self.tweak_tabs=QTabWidget(); lay.addWidget(self.tweak_tabs); self.tabs.addTab(self.tweak_tab,"Tweaks")
 def refresh(self):
  i=get_system_info(); self.system.setText(f"Windows: {i['windows']} | Build: {i['build']} | CPU: {i['cpu']} | GPU: {i['gpu']} | RAM: {i['ram_gb']} GB | Disk: {i['disk']} | Device: {i['device_type']}"); self.admin.setText("Administrator" if i["admin"] else "Standard user"); self.tweaks=all_tweaks(); self._render_tweaks(); self.output.setPlainText(f"SCAN COMPLETE\n{len(self.tweaks)} operations available • {sum(t.recommended for t in self.tweaks)} recommended")
 def _render_tweaks(self):
  self.tweak_tabs.clear(); self.checks=[]; groups={}
  for t in self.tweaks: groups.setdefault(t.category,[]).append(t)
  for cat,items in groups.items():
   page=QWidget(); lay=QVBoxLayout(page); scroll=QScrollArea(); scroll.setWidgetResizable(True); inner=QWidget(); il=QVBoxLayout(inner)
   for t in items:
    box=QGroupBox(); bl=QVBoxLayout(box); cb=QCheckBox(t.name); cb.setChecked(t.recommended); cb.setProperty("tweak_id",t.id); bl.addWidget(cb); d=QLabel(f"{t.description}\nRisk: {t.risk} • Reversible: {'Yes' if t.reversible else 'No'} • Restart: {t.restart}"); d.setWordWrap(True); bl.addWidget(d); il.addWidget(box); self.checks.append(cb)
   il.addStretch(); scroll.setWidget(inner); lay.addWidget(scroll); self.tweak_tabs.addTab(page,cat)
 def _build_software_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); buttons=QHBoxLayout()
  for text,fn in [("Installed",self.show_software),("Upgrade All",self.upgrade_software)]: b=QPushButton(text); b.clicked.connect(fn); buttons.addWidget(b)
  lay.addLayout(buttons); self.apps=QListWidget(); lay.addWidget(self.apps); self.tabs.addTab(page,"Software")
  for pid,name,cat in CATALOG: item=QListWidgetItem(f"{name}  •  {cat}  •  {pid}"); item.setData(32,pid); self.apps.addItem(item)
  self.apps.itemDoubleClicked.connect(self.install_selected)
 def _build_updates_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); b=QPushButton("Check for WinGet upgrades"); b.clicked.connect(self.check_updates); lay.addWidget(b); self.tabs.addTab(page,"Updates")
 def _build_repairs_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); info=QLabel("Repairs can take several minutes. Run DISM/SFC only when troubleshooting system corruption."); info.setWordWrap(True); lay.addWidget(info)
  for text,fn in [("Restart Explorer",self.repair_explorer),("Run SFC /scannow",self.repair_sfc),("Run DISM RestoreHealth",self.repair_dism)]: b=QPushButton(text); b.clicked.connect(fn); lay.addWidget(b)
  self.tabs.addTab(page,"Fixes")
 def create_backup(self):
  try:self.output.setPlainText(f"BACKUP CREATED\n{self.backup.create()}")
  except Exception as e:QMessageBox.critical(self,"Backup failed",str(e))
 def restore_point(self):
  if not is_admin(): QMessageBox.warning(self,"Administrator required","Run Windows Optimizer as Administrator."); return
  try:self.output.setPlainText(create_restore_point())
  except Exception as e:QMessageBox.critical(self,"Restore point failed",str(e))
 def apply_selected(self):
  if not is_admin(): QMessageBox.warning(self,"Administrator required","Run as Administrator before applying changes."); return
  ids={c.property("tweak_id") for c in self.checks if c.isChecked()}; selected=[t for t in self.tweaks if t.id in ids and t.apply]
  if not selected:return QMessageBox.information(self,"Nothing selected","Select at least one tweak.")
  if QMessageBox.question(self,"Confirm",f"Apply {len(selected)} selected operation(s)? A registry backup will be created first.")!=QMessageBox.StandardButton.Yes:return
  self.backup.create(); results=self.executor.apply(selected); self.output.setPlainText("\n".join(f"{r.tweak_id}: {r.status} — {r.message}" for r in results)); self.refresh()
 def show_software(self):
  try:self.output.setPlainText(installed_apps())
  except Exception as e:self.output.setPlainText(str(e))
 def install_selected(self,item=None):
  item=item or self.apps.currentItem()
  if not item:return
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator to install software.")
  pid=item.data(32)
  if QMessageBox.question(self,"Install",f"Install {pid} using WinGet?")!=QMessageBox.StandardButton.Yes:return
  try:self.output.setPlainText(install(pid))
  except Exception as e:self.output.setPlainText(f"Install failed: {e}")
 def upgrade_software(self):
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator to upgrade software.")
  try:self.output.setPlainText(upgrade_all())
  except Exception as e:self.output.setPlainText(f"Upgrade failed: {e}")
 def check_updates(self):
  try:self.output.setPlainText(scan_updates())
  except Exception as e:self.output.setPlainText(str(e))
 def repair_explorer(self):
  try:self.output.setPlainText(explorer())
  except Exception as e:self.output.setPlainText(str(e))
 def repair_sfc(self):
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator.")
  try:self.output.setPlainText(sfc())
  except Exception as e:self.output.setPlainText(str(e))
 def repair_dism(self):
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator.")
  try:self.output.setPlainText(dism())
  except Exception as e:self.output.setPlainText(str(e))
