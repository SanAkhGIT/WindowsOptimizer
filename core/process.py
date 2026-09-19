import subprocess
from core.logging import get_logger
from dataclasses import dataclass

@dataclass
class ProcessResult:
    returncode:int
    stdout:str
    stderr:str

def run_executable(executable,args=(),timeout=120):
    logger = get_logger("process")
    command = [str(executable), *(str(arg) for arg in args)]
    logger.info("Process started | executable=%s | args=%r | timeout=%s", executable, args, timeout)
    try:
        p = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
    except Exception:
        logger.exception("Process failed to start | executable=%s", executable)
        raise

    stdout = p.stdout.strip()
    stderr = p.stderr.strip()
    logger.info(
        "Process finished | executable=%s | returncode=%s | stdout=%r | stderr=%r",
        executable,
        p.returncode,
        stdout[-4000:],
        stderr[-4000:],
    )
    return ProcessResult(p.returncode, stdout, stderr)
