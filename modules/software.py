from core.process import run_executable

CATALOG=[
 ("7zip.7zip","7-Zip","Utilities"),("Google.Chrome","Google Chrome","Browsers"),("Mozilla.Firefox","Mozilla Firefox","Browsers"),("VideoLAN.VLC","VLC","Media"),("Notepad++.Notepad++","Notepad++","Development"),("Microsoft.VisualStudioCode","Visual Studio Code","Development"),("Git.Git","Git","Development"),("Microsoft.PowerToys","PowerToys","Utilities"),("Discord.Discord","Discord","Communication"),("WinSCP.WinSCP","WinSCP","Utilities")
]

def _winget(args,timeout=180):
 r=run_executable("winget",args,timeout); return r.stdout or r.stderr, r.returncode

def installed_apps():
 out,code=_winget(["list","--accept-source-agreements"],90)
 if code and not out: raise RuntimeError("WinGet inventory unavailable. Install/repair App Installer first.")
 return out

def upgrade_available():
 out,code=_winget(["upgrade","--accept-source-agreements"],120)
 if code and not out: raise RuntimeError("WinGet upgrade inventory unavailable.")
 return out

def install(package_id):
 if not any(package_id==row[0] for row in CATALOG): raise ValueError("Package is not in the curated catalog.")
 out,code=_winget(["install","--id",package_id,"--exact","--accept-package-agreements","--accept-source-agreements"],300)
 if code: raise RuntimeError(out or f"WinGet failed for {package_id}.")
 return out or f"Installed {package_id}."

def upgrade_all():
 out,code=_winget(["upgrade","--all","--accept-package-agreements","--accept-source-agreements"],600)
 if code and "No applicable upgrade found" not in out: raise RuntimeError(out or "WinGet upgrade failed.")
 return out or "No applicable upgrades found."
