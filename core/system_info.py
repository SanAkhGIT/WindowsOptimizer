import ctypes,platform,subprocess,psutil

def is_admin():
 try:return bool(ctypes.windll.shell32.IsUserAnAdmin())
 except Exception:return False

def _ps(cmd):
 p=subprocess.run(["powershell.exe","-NoProfile","-NonInteractive","-ExecutionPolicy","Bypass","-Command",cmd],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=30); return p.stdout.strip()

def get_system_info():
 cpu=platform.processor() or "Unknown"; gpu=disk="Unknown"; device="Desktop"
 try:
  v=_ps("(Get-CimInstance Win32_Processor|select -First 1 -Expand Name)"); cpu=v or cpu
  v=_ps("(Get-CimInstance Win32_VideoController|select -First 1 -Expand Name)"); gpu=v or gpu
  v=_ps("(Get-PhysicalDisk|select -First 1 -Expand MediaType)"); disk=v or disk
  v=_ps("(Get-CimInstance Win32_SystemEnclosure|select -First 1 -Expand ChassisTypes)"); device="Laptop" if any(x in v for x in ["8","9","10","11","12","14","18","21"]) else device
 except Exception: pass
 return {"windows":platform.platform(),"build":platform.version(),"cpu":cpu,"gpu":gpu,"disk":disk,"ram_gb":round(psutil.virtual_memory().total/1073741824,1),"device_type":device,"admin":is_admin(),"battery":bool(psutil.sensors_battery())}
