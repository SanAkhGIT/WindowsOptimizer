import json
from core.process import run_executable

def inventory():
    ps=(r"Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,StartName,PathName | ConvertTo-Json -Compress")
    r=run_executable("powershell.exe",["-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",ps],120)
    if r.returncode: raise RuntimeError(r.stderr or "Service inventory failed.")
    return r.stdout or "[]"

def records():
    try: value=json.loads(inventory())
    except json.JSONDecodeError as exc: raise RuntimeError(f"Service inventory returned invalid JSON: {exc}") from exc
    if isinstance(value,dict): value=[value]
    return [{**item,"classification":classify(item),"recommendation":recommendation(item)} for item in value]

def classify(service):
    text=" ".join(str(service.get(k,"") or "") for k in ("Name","DisplayName","PathName","StartName")).lower()
    if any(x in text for x in ("microsoft",r"\windows\","windows\")): return "Windows"
    if any(x in text for x in ("intel","amd","nvidia","realtek","oem")): return "Hardware/OEM"
    return "Third-party/Unknown"

def recommendation(service):
    if str(service.get("StartMode","")).lower()=="disabled":
        return "Already disabled; no action suggested."
    if classify(service)=="Windows":
        return "Leave unchanged unless a specific Windows issue is being diagnosed."
    if classify(service)=="Hardware/OEM":
        return "Review only if the associated hardware/software is unused."
    return "Review publisher, path and dependency before changing startup mode."
