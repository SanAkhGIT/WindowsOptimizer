from pathlib import Path
from datetime import datetime
import json,winreg
BASE=Path.home()/"WindowsOptimizerBackups"
class BackupManager:
 def create(self):
  path=BASE/datetime.now().strftime("%Y-%m-%d_%H-%M-%S"); path.mkdir(parents=True,exist_ok=True); reg={}
  checks=[(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced","TaskbarAl"),(winreg.HKEY_CURRENT_USER,r"Control Panel\Desktop","WallPaper"),(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize","EnableTransparency"),(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\GameBar","AutoGameModeEnabled"),(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled"),(winreg.HKEY_CURRENT_USER,r"System\GameConfigStore","GameDVR_Enabled"),(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo","Enabled")]
  for root,key,val in checks:
   try:
    with winreg.OpenKey(root,key,0,winreg.KEY_READ) as k: reg[f"{root}:{key}:{val}"]=winreg.QueryValueEx(k,val)[0]
   except FileNotFoundError: reg[f"{root}:{key}:{val}"]=None
  (path/"registry_snapshot.json").write_text(json.dumps(reg,indent=2,default=str),encoding="utf-8"); return path
