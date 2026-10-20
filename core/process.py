import locale
import subprocess
import sys
import time
from dataclasses import dataclass

from core.logging import get_logger


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


def hidden_console_kwargs():
    """Return subprocess options that prevent helper consoles from flashing on Windows."""
    if sys.platform != "win32":
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startupinfo.wShowWindow = subprocess.SW_HIDE
    return {
        "creationflags": subprocess.CREATE_NO_WINDOW,
        "startupinfo": startupinfo,
    }


def _decode_output(data):
    """Decode Windows command output without corrupting OEM-console text."""
    if not data:
        return ""

    raw = bytes(data)
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            pass

    if sys.platform == "win32":
        # Classic Windows repair tools such as SFC/DISM commonly emit using
        # the active OEM code page rather than UTF-8.
        for encoding in ("oem", "mbcs"):
            try:
                return raw.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                pass

    encoding = locale.getpreferredencoding(False) or "utf-8"
    return raw.decode(encoding, errors="replace")


def run_executable(executable, args=(), timeout=120):
    logger = get_logger("process")
    command = [str(executable), *(str(arg) for arg in args)]
    started = time.monotonic()
    logger.info(
        "Process started | executable=%s | args=%r | timeout=%s",
        executable,
        args,
        timeout,
    )
    try:
        p = subprocess.run(
            command,
            capture_output=True,
            text=False,
            timeout=timeout,
            **hidden_console_kwargs(),
        )
    except subprocess.TimeoutExpired:
        logger.exception("Process timed out | executable=%s | timeout=%s | elapsed=%.2fs", executable, timeout, time.monotonic() - started)
        raise
    except Exception:
        logger.exception("Process failed to start | executable=%s | elapsed=%.2fs", executable, time.monotonic() - started)
        raise

    stdout = _decode_output(p.stdout).strip()
    stderr = _decode_output(p.stderr).strip()
    logger.info(
        "Process finished | executable=%s | returncode=%s | duration=%.2fs | stdout=%r | stderr=%r",
        executable,
        p.returncode,
        time.monotonic() - started,
        stdout[-4000:],
        stderr[-4000:],
    )
    return ProcessResult(p.returncode, stdout, stderr)
