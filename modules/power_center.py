from core.process import run_executable

PLANS = {"Balanced": "SCHEME_BALANCED", "Power saver": "SCHEME_MAX", "High performance": "SCHEME_MIN"}

def current():
    r=run_executable("powercfg.exe",("/GETACTIVESCHEME",),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to read active power plan.")
    return r.stdout or "No active plan."

def plans():
    r=run_executable("powercfg.exe",("/LIST",),30)
    if r.returncode: raise RuntimeError(r.stderr or "Unable to enumerate power plans.")
    return r.stdout or "No power plans."

def activate(name):
    if name not in PLANS: raise ValueError("Unsupported power plan.")
    r=run_executable("powercfg.exe",("/SETACTIVE",PLANS[name]),30)
    if r.returncode: raise RuntimeError(r.stderr or f"Unable to activate {name}.")
    return f"{name} power plan activated."

def battery_report():
    path=str(__import__("pathlib").Path.home()/"WindowsOptimizerBackups"/"battery-report.html")
    r=run_executable("powercfg.exe",("/BATTERYREPORT","/OUTPUT",path),60)
    if r.returncode: raise RuntimeError(r.stderr or "Battery report failed.")
    return f"Battery report: {path}"
