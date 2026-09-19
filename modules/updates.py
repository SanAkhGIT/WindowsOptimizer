from core.process import run_executable

def scan():
 r=run_executable("winget",["upgrade","--accept-source-agreements"],120)
 return r.stdout or r.stderr

def upgrade_all():
 r=run_executable("winget",["upgrade","--all","--accept-package-agreements","--accept-source-agreements"],600)
 if r.returncode and "No applicable upgrade found" not in (r.stdout+r.stderr): raise RuntimeError(r.stderr or r.stdout or "Upgrade failed.")
 return r.stdout or r.stderr or "No applicable upgrades found."
