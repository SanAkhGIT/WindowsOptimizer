from core.process import run_executable

def explorer():
 r=run_executable("taskkill",["/f","/im","explorer.exe"],30)
 if r.returncode not in (0,128): raise RuntimeError(r.stderr or r.stdout)
 run_executable("explorer.exe",[],30); return "Explorer restarted."

def sfc():
 r=run_executable("sfc.exe",["/scannow"],1800)
 if r.returncode: raise RuntimeError(r.stderr or r.stdout or "SFC failed.")
 return r.stdout or "SFC completed."

def dism():
 r=run_executable("DISM.exe",["/Online","/Cleanup-Image","/RestoreHealth"],1800)
 if r.returncode: raise RuntimeError(r.stderr or r.stdout or "DISM failed.")
 return r.stdout or "DISM completed."
