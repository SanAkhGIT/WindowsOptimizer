import winreg
from core.models import Tweak
from core.registry import read_value,write_dword

def game_on():
 v=read_value(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\GameBar","AutoGameModeEnabled"); return v is not None and v[0]==1

def game_apply(): write_dword(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\GameBar","AutoGameModeEnabled",1); return "Windows Game Mode preference enabled."

def dvr_apply():
 write_dword(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\GameDVR","AppCaptureEnabled",0); write_dword(winreg.HKEY_CURRENT_USER,r"System\GameConfigStore","GameDVR_Enabled",0); return "Game DVR capture disabled for the current user."

def scan(): return [Tweak("game_mode","Enable Windows Game Mode","Gaming","Enables Microsoft's built-in Game Mode preference.","SAFE",not game_on(),False,False,"None",game_on,game_apply),Tweak("game_dvr_off","Disable Game DVR capture","Gaming","Stops background Game DVR capture if you do not record gameplay.","CAUTION",False,True,False,"None",None,dvr_apply)]
