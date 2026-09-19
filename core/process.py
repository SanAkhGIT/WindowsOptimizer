import subprocess
from dataclasses import dataclass

@dataclass
class ProcessResult:
    returncode:int
    stdout:str
    stderr:str

def run_executable(executable,args=(),timeout=120):
    p=subprocess.run([executable,*args],capture_output=True,text=True,encoding="utf-8",errors="replace",timeout=timeout)
    return ProcessResult(p.returncode,p.stdout.strip(),p.stderr.strip())
