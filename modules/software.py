from core.diagnostics import run_command
def installed_apps():
 code,out,err=run_command("winget list --accept-source-agreements",90)
 if code and not out: raise RuntimeError(err or "WinGet inventory unavailable.")
 return out
