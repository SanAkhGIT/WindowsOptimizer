from core.process import run_executable

def current():
    r=run_executable("powercfg.exe",["/GETACTIVESCHEME"],30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to read active power plan.")
    return r.stdout or "No active power plan reported."

def plans():
    r=run_executable("powercfg.exe",["/LIST"],30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to enumerate power plans.")
    return r.stdout or "No power plans reported."

def set_high_performance():
    r=run_executable("powercfg.exe",["/SETACTIVE","SCHEME_MIN"],30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to activate High Performance.")
    return "High Performance power plan activated."
