from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QTextEdit,QCheckBox,QMessageBox,QTabWidget,QGroupBox,QScrollArea,QProgressBar
from core.system_info import get_system_info,is_admin
from core.backup import BackupManager
from core.executor import Executor
from core.restore import create_restore_point
from modules.catalog import all_tweaks
from modules.software import installed_apps
class MainWindow(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle("Windows Optimizer"); self.resize(1180,780); self.backup=BackupManager(); self.executor=Executor(); self._build_ui(); self.refresh()
 def _build_ui(self):
  c=QWidget(); self.setCentralWidget(c); root=QVBoxLayout(c); h=QHBoxLayout(); t=QLabel("Windows Optimizer"); t.setStyleSheet("font-size:26px;font-weight:700;"); h.addWidget(t); h.addStretch(); self.admin=QLabel(); h.addWidget(self.admin); root.addLayout(h); self.system=QLabel(); self.system.setWordWrap(True); root.addWidget(self.system)
  a=QHBoxLayout()
  for label,fn in [("Scan",self.refresh),("Create Backup",self.create_backup),("Restore Point",self.restore_point),("Apply Selected",self.apply_selected),("WinGet Inventory",self.show_software)]:
   b=QPushButton(label); b.clicked.connect(fn); a.addWidget(b)
  root.addLayout(a); self.progress=QProgressBar(); self.progress.setVisible(False); root.addWidget(self.progress); self.tabs=QTabWidget(); root.addWidget(self.tabs,1); self.output=QTextEdit(); self.output.setReadOnly(True); self.output.setMaximumHeight(150); root.addWidget(self.output)
 def refresh(self):
  i=get_system_info(); self.system.setText(f"Windows: {i['windows']} | Build: {i['build']} | CPU: {i['cpu']} | GPU: {i['gpu']} | RAM: {i['ram_gb']} GB | Disk: {i['disk']} | Device: {i['device_type']}"); self.admin.setText("Administrator" if i["admin"] else "Standard user"); self.tweaks=all_tweaks(); self._render(); self.output.setPlainText(f"SCAN COMPLETE\n{len(self.tweaks)} operations available • {sum(t.recommended for t in self.tweaks)} recommended")
 def _render(self):
  self.tabs.clear(); self.checks=[]; groups={}
  for t in self.tweaks: groups.setdefault(t.category,[]).append(t)
  for cat,items in groups.items():
   page=QWidget(); lay=QVBoxLayout(page); scroll=QScrollArea(); scroll.setWidgetResizable(True); inner=QWidget(); il=QVBoxLayout(inner)
   for t in items:
    box=QGroupBox(); bl=QVBoxLayout(box); cb=QCheckBox(t.name); cb.setChecked(t.recommended); cb.setProperty("tweak_id",t.id); bl.addWidget(cb); d=QLabel(f"{t.description}\nRisk: {t.risk} • Reversible: {'Yes' if t.reversible else 'No'} • Restart: {t.restart}"); d.setWordWrap(True); bl.addWidget(d); il.addWidget(box); self.checks.append(cb)
   il.addStretch(); scroll.setWidget(inner); lay.addWidget(scroll); self.tabs.addTab(page,cat)
 def create_backup(self):
  try:self.output.setPlainText(f"BACKUP CREATED\n{self.backup.create()}")
  except Exception as e:QMessageBox.critical(self,"Backup failed",str(e))
 def restore_point(self):
  if not is_admin(): QMessageBox.warning(self,"Administrator required","Run Windows Optimizer as Administrator."); return
  try:self.output.setPlainText(create_restore_point())
  except Exception as e:QMessageBox.critical(self,"Restore point failed",str(e))
 def apply_selected(self):
  if not is_admin(): QMessageBox.warning(self,"Administrator required","Restart this application as Administrator before applying changes."); return
  ids={c.property("tweak_id") for c in self.checks if c.isChecked()}; selected=[t for t in self.tweaks if t.id in ids and t.apply]
  if not selected: QMessageBox.information(self,"Nothing selected","Select at least one operation."); return
  if QMessageBox.question(self,"Confirm changes",f"Apply {len(selected)} selected operation(s)? A registry backup will be created first.")!=QMessageBox.StandardButton.Yes:return
  self.backup.create(); results=self.executor.apply(selected); self.output.setPlainText("\n".join(f"{r.tweak_id}: {r.status} — {r.message}" for r in results)); self.refresh()
 def show_software(self):
  try:self.output.setPlainText(installed_apps() or "WinGet returned no installed applications.")
  except Exception as e:self.output.setPlainText(f"WinGet inventory unavailable: {e}")
