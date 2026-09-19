import locale
import subprocess
import sys
from dataclasses import dataclass

from core.logging import get_logger


@dataclass
class ProcessResult:
    returncode: int
    stdout: str
    stderr: str


def _decode_output(data):
    """Decode Windows command output without corrupting OEM-console text."""
    if not data:
        return ""

    raw = bytes(data)
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        for encoding in ("utf-16", "utf-16-le", "utf-16-be"):
            try:
                return raw.decode(encoding)
            except UnicodeDecodeError:
                pass

    # Some classic Windows utilities emit UTF-16LE without a BOM when stdout
    # is redirected. A high NUL-byte ratio is a reliable indicator.
    if raw.count(b"\x00") >= max(2, len(raw) // 4):
        try:
            return raw.decode("utf-16-le")
        except UnicodeDecodeError:
            pass

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
        )
    except Exception:
        logger.exception("Process failed to start | executable=%s", executable)
        raise

    stdout = _decode_output(p.stdout).strip()
    stderr = _decode_output(p.stderr).strip()
    logger.info(
        "Process finished | executable=%s | returncode=%s | stdout=%r | stderr=%r",
        executable,
        p.returncode,
        stdout[-4000:],
        stderr[-4000:],
    )
    return ProcessResult(p.returncode, stdout, stderr)
