import subprocess

def create_restore_point(description="WindowsOptimizer"):
    script="$ErrorActionPreference='Stop'; Checkpoint-Computer -Description '"+description.replace("'","''")+"' -RestorePointType 'MODIFY_SETTINGS'"
    p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",script],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=90)
    if p.returncode: raise RuntimeError(p.stderr.strip() or p.stdout.strip() or "Restore point creation failed.")
    return "System Restore point created."
