import subprocess

def run_command(command,timeout=120):
 p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",command],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout); return p.returncode,p.stdout.strip(),p.stderr.strip()
