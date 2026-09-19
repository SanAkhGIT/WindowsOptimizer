from PySide6.QtWidgets import QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QPushButton,QLabel,QTextEdit,QCheckBox,QMessageBox,QTabWidget,QGroupBox,QScrollArea,QListWidget,QListWidgetItem,QComboBox
from core.system_info import get_system_info,is_admin
from core.backup import BackupManager
from core.executor import Executor
from core.restore import create_restore_point
from core.jobs import JobRunner
from core.profiles import load_profiles
from modules.catalog import all_tweaks
from modules.operations import profile_tweaks
from modules.software import installed_apps,CATALOG,install,upgrade_all
from modules.updates import scan as scan_updates
from modules.repair import explorer,sfc,dism
from modules.startup import inventory as startup_inventory
from modules.power import current as power_current, plans as power_plans, set_high_performance
from modules.network_center import adapters as network_adapters, configuration as network_configuration, latency as network_latency
from ui.system_dashboard import SystemDashboard
from modules.services import inventory as services_inventory

class MainWindow(QMainWindow):
 def __init__(self):
  super().__init__(); self.setWindowTitle("Windows Optimizer"); self.resize(1200,820); self.backup=BackupManager(); self.executor=Executor(); self.jobs=JobRunner(); self._busy=False; self._build_ui(); self.refresh()
 def _build_ui(self):
  c=QWidget(); self.setCentralWidget(c); root=QVBoxLayout(c)
  h=QHBoxLayout(); t=QLabel("Windows Optimizer"); t.setStyleSheet("font-size:26px;font-weight:700;"); h.addWidget(t); h.addStretch(); self.admin=QLabel(); h.addWidget(self.admin); root.addLayout(h)
  self.system=QLabel(); self.system.setWordWrap(True); root.addWidget(self.system)
  bar=QHBoxLayout()
  for text,fn in [("Scan",self.refresh), ("Backup",self.create_backup), ("Restore Point",self.restore_point), ("Apply Selected",self.apply_selected)]:
   b=QPushButton(text); b.clicked.connect(fn); bar.addWidget(b)
  root.addLayout(bar); self.tabs=QTabWidget(); root.addWidget(self.tabs); self.output=QTextEdit(); self.output.setReadOnly(True); self.output.setMaximumHeight(180); root.addWidget(self.output)
  self._build_tweaks_tab(); self._build_software_tab(); self._build_updates_tab(); self._build_repairs_tab(); self._build_windows_tab()
 def _build_tweaks_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); controls=QHBoxLayout(); self.profile=QComboBox(); self.profile.addItem("Custom",None)
  for p in load_profiles(): self.profile.addItem(p.get("name",p["id"]),p)
  self.profile.currentIndexChanged.connect(self.select_profile); controls.addWidget(self.profile)
  for text,fn in [("Recommended",self.select_recommended),("Clear",self.clear_selection)]: b=QPushButton(text); b.clicked.connect(fn); controls.addWidget(b)
  controls.addStretch(); lay.addLayout(controls); self.tweak_tabs=QTabWidget(); lay.addWidget(self.tweak_tabs); self.tabs.addTab(page,"Tweaks")
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
 def _set_ids(self,ids):
  ids=set(ids)
  for cb in self.checks: cb.setChecked(cb.property("tweak_id") in ids)
 def select_profile(self,index):
  profile=self.profile.itemData(index)
  if profile:self._set_ids(profile.get("tweaks",[]))
 def select_recommended(self): self._set_ids(t.id for t in self.tweaks if t.recommended)
 def clear_selection(self): self._set_ids([])
 def create_backup(self):
  try:self.output.setPlainText(f"BACKUP CREATED\n{self.backup.create()}")
  except Exception as e:QMessageBox.critical(self,"Backup failed",str(e))
 def restore_point(self):
  if not is_admin(): QMessageBox.warning(self,"Administrator required","Run Windows Optimizer as Administrator."); return
  self._run_job(create_restore_point,done=self._show_result,fail=self._show_error)
 def apply_selected(self):
  if self._busy:return
  if not is_admin(): QMessageBox.warning(self,"Administrator required","Run as Administrator before applying changes."); return
  ids={c.property("tweak_id") for c in self.checks if c.isChecked()}; selected=[t for t in self.tweaks if t.id in ids and t.apply]
  if not selected:return QMessageBox.information(self,"Nothing selected","Select at least one tweak.")
  if QMessageBox.question(self,"Confirm",f"Apply {len(selected)} selected operation(s)? A registry backup will be created first.")!=QMessageBox.StandardButton.Yes:return
  try:self.backup.create()
  except Exception as e:return QMessageBox.critical(self,"Backup failed",str(e))
  self._run_job(self.executor.apply,selected,done=self._show_apply_results,fail=self._show_error)
 def _run_job(self,fn,*args,done=None,fail=None):
  self._busy=True; self._set_enabled(False); signals=self.jobs.submit(fn,*args); signals.finished.connect(lambda value:(done(value) if done else None,self._job_done())); signals.failed.connect(lambda error:(fail(error) if fail else None,self._job_done()))
 def _job_done(self): self._busy=False; self._set_enabled(True)
 def _set_enabled(self,enabled):
  for w in self.findChildren(QPushButton): w.setEnabled(enabled)
 def _show_result(self,value): self.output.setPlainText(str(value))
 def _show_error(self,error): self.output.setPlainText(f"Operation failed:\n{error}")
 def _show_apply_results(self,results): self.output.setPlainText("\n".join(f"{r.tweak_id}: {r.status} — {r.message} — {r.verification}" for r in results)); self.refresh()
 def _build_windows_tab(self):
  page=QWidget(); lay=QVBoxLayout(page)
  info=QLabel("Windows management is primarily diagnostic here. Changes are kept explicit instead of applying broad system-wide presets.")
  info.setWordWrap(True); lay.addWidget(info)
  row=QHBoxLayout()
  for text,fn in [("Startup Inventory",self.show_startup),("Services",self.show_services),("Power Plans",self.show_power),("Network Adapters",self.show_network),("Network Config",self.show_network_config),("Ping 1.1.1.1",self.show_latency)]:
   b=QPushButton(text); b.clicked.connect(fn); row.addWidget(b)
  lay.addLayout(row)
  b=QPushButton("Activate High Performance Power Plan"); b.clicked.connect(self.enable_high_performance); lay.addWidget(b)
  self.tabs.addTab(page,"Windows")
 def show_startup(self): self._run_job(startup_inventory,done=self._show_result,fail=self._show_error)
 def show_services(self): self._run_job(services_inventory,done=self._show_result,fail=self._show_error)
 def show_power(self): self._run_job(lambda: power_current()+"\n\nAvailable plans:\n"+power_plans(),done=self._show_result,fail=self._show_error)
 def show_network(self): self._run_job(network_adapters,done=self._show_result,fail=self._show_error)
 def show_network_config(self): self._run_job(network_configuration,done=self._show_result,fail=self._show_error)
 def show_latency(self): self._run_job(network_latency,done=self._show_result,fail=self._show_error)
 def enable_high_performance(self):
  if not is_admin(): return QMessageBox.warning(self,"Administrator required","Run as Administrator to change the active power plan.")
  if QMessageBox.question(self,"Power plan","Activate High Performance for this Windows installation?")!=QMessageBox.StandardButton.Yes:return
  self._run_job(set_high_performance,done=self._show_result,fail=self._show_error)
 def _build_software_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); buttons=QHBoxLayout()
  for text,fn in [("Installed",self.show_software),("Upgrade All",self.upgrade_software)]: b=QPushButton(text); b.clicked.connect(fn); buttons.addWidget(b)
  lay.addLayout(buttons); self.apps=QListWidget(); lay.addWidget(self.apps); self.tabs.addTab(page,"Software")
  for pid,name,cat in CATALOG: item=QListWidgetItem(f"{name}  •  {cat}  •  {pid}"); item.setData(32,pid); self.apps.addItem(item)
  self.apps.itemDoubleClicked.connect(self.install_selected)
 def _build_updates_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); b=QPushButton("Check for WinGet upgrades"); b.clicked.connect(self.check_updates); lay.addWidget(b); self.tabs.addTab(page,"Updates")
 def _build_repairs_tab(self):
  page=QWidget(); lay=QVBoxLayout(page); info=QLabel("Repairs can take several minutes. SFC/DISM should be used for troubleshooting, not as routine optimization."); info.setWordWrap(True); lay.addWidget(info)
  for text,fn in [("Restart Explorer",self.repair_explorer),("Run SFC /scannow",self.repair_sfc),("Run DISM RestoreHealth",self.repair_dism)]: b=QPushButton(text); b.clicked.connect(fn); lay.addWidget(b)
  self.tabs.addTab(page,"Fixes")
 def show_software(self): self._run_job(installed_apps,done=self._show_result,fail=self._show_error)
 def install_selected(self,item=None):
  item=item or self.apps.currentItem()
  if not item:return
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator to install software.")
  pid=item.data(32)
  if QMessageBox.question(self,"Install",f"Install {pid} using WinGet?")!=QMessageBox.StandardButton.Yes:return
  self._run_job(install,pid,done=self._show_result,fail=self._show_error)
 def upgrade_software(self):
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator to upgrade software.")
  self._run_job(upgrade_all,done=self._show_result,fail=self._show_error)
 def check_updates(self): self._run_job(scan_updates,done=self._show_result,fail=self._show_error)
 def repair_explorer(self): self._run_job(explorer,done=self._show_result,fail=self._show_error)
 def repair_sfc(self):
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator.")
  self._run_job(sfc,done=self._show_result,fail=self._show_error)
 def repair_dism(self):
  if not is_admin():return QMessageBox.warning(self,"Administrator required","Run as Administrator.")
  self._run_job(dism,done=self._show_result,fail=self._show_error)
