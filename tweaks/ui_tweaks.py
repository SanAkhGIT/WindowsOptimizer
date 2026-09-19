import winreg
from core.registry import read_value,write_dword
from core.models import Tweak
ADV=r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced"; PERSONALIZE=r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
def left_state():
 v=read_value(winreg.HKEY_CURRENT_USER,ADV,"TaskbarAl"); return v is not None and v[0]==0
def trans_state():
 v=read_value(winreg.HKEY_CURRENT_USER,PERSONALIZE,"EnableTransparency"); return v is not None and v[0]==0
def left(): write_dword(winreg.HKEY_CURRENT_USER,ADV,"TaskbarAl",0); return "Taskbar alignment set to left."
def trans(): write_dword(winreg.HKEY_CURRENT_USER,PERSONALIZE,"EnableTransparency",0); return "Transparency disabled."
def scan_ui_tweaks(): return [Tweak("taskbar_left","Left-align taskbar","UI","Use the Windows 11 taskbar alignment setting.","SAFE",not left_state(),False,False,"Explorer restart may be required.",left_state,left),Tweak("transparency_off","Disable transparency","Performance","Reduce transparency effects for a simpler desktop composition.","SAFE",not trans_state(),False,False,"None",trans_state,trans)]
