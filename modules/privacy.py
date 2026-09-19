import winreg
from core.models import Tweak
from core.registry import read_value,write_dword
KEY=r"Software\Microsoft\Windows\CurrentVersion\AdvertisingInfo"
def off():
 v=read_value(winreg.HKEY_CURRENT_USER,KEY,"Enabled"); return v is not None and v[0]==0
def apply(): write_dword(winreg.HKEY_CURRENT_USER,KEY,"Enabled",0); return "Advertising ID disabled for the current user."
def scan(): return [Tweak("advertising_id_off","Disable advertising ID","Privacy","Stops Windows from using the per-user advertising ID for app personalization.","SAFE",not off(),True,False,"None",off,apply)]
