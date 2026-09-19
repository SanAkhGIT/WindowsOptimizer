from pathlib import Path
from PIL import Image
from core.models import Tweak
import ctypes,winreg
ASSET_DIR=Path(__file__).resolve().parent.parent/"assets"/"generated"
def black():
 ASSET_DIR.mkdir(parents=True,exist_ok=True); p=ASSET_DIR/"black-desktop.png"
 if not p.exists(): Image.new("RGB",(3840,2160),(0,0,0)).save(p,"PNG")
 return p
def apply():
 p=black(); k=winreg.CreateKey(winreg.HKEY_CURRENT_USER,r"Control Panel\Desktop"); winreg.SetValueEx(k,"WallPaper",0,winreg.REG_SZ,str(p)); winreg.CloseKey(k); ctypes.windll.user32.SystemParametersInfoW(20,0,str(p),3); return "Desktop wallpaper set to pure black."
def scan_personalization(): return [Tweak("black_wallpaper","Pure black desktop wallpaper","UI","Use an application-generated #000000 wallpaper.","SAFE",False,True,False,"None",None,apply,metadata={"path":str(black())})]
