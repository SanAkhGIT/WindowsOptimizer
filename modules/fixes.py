from core.models import Tweak
from core.diagnostics import run_command

def explorer():
 code,out,err=run_command("Stop-Process -Name explorer -Force -ErrorAction SilentlyContinue; Start-Process explorer.exe")
 if code: raise RuntimeError(err or out or "Explorer restart failed.")
 return "Windows Explorer restarted."
def scan(): return [Tweak("restart_explorer","Restart Windows Explorer","Fixes","Reloads Explorer after UI changes.","SAFE",False,False,False,"None",None,explorer)]
