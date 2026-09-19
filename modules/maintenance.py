"""Safe, non-interactive daily maintenance routines for WindowsOptimizer."""

from __future__ import annotations

import json
import os
import shutil
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from datetime import datetime, timezone

import psutil


@dataclass
class MaintenanceResult:
    name: str
    status: str
    message: str
    reclaimed_bytes: int = 0
    details: dict | None = None


HOURS_OLD_FOR_TEMP = 48
DAYS_OLD_FOR_DUMPS = 14
HISTORY_DIR = Path(os.environ.get("LOCALAPPDATA", Path.home())) / "WindowsOptimizer" / "Maintenance"
HISTORY_FILE = HISTORY_DIR / "history.jsonl"


def _is_admin() -> bool:
    try:
        import ctypes
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except (AttributeError, OSError):
        return False


def _safe_delete_tree(path: Path, cutoff: float) -> tuple[int, int]:
    """Delete old files/directories without following reparse points."""
    reclaimed = 0
    deleted = 0
    if not path.is_dir():
        return reclaimed, deleted

    for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
        root_path = Path(root)
        for filename in files:
            file_path = root_path / filename
            try:
                if file_path.is_symlink() or file_path.stat().st_mtime >= cutoff:
                    continue
                size = file_path.stat().st_size
                file_path.unlink()
                reclaimed += size
                deleted += 1
            except (FileNotFoundError, PermissionError, OSError):
                continue

        for dirname in dirs:
            directory = root_path / dirname
            try:
                if directory.is_symlink():
                    continue
                if not any(directory.iterdir()) and directory.stat().st_mtime < cutoff:
                    directory.rmdir()
            except (FileNotFoundError, PermissionError, OSError):
                continue
    return reclaimed, deleted


def _user_profiles() -> list[Path]:
    users = Path(os.environ.get("SystemDrive", "C:")) / "Users"
    if not users.is_dir():
        return []
    ignored = {"Public", "Default", "Default User", "All Users"}
    return [
        p for p in users.iterdir()
        if p.is_dir() and p.name not in ignored and not p.is_symlink()
    ]


def clean_temp() -> MaintenanceResult:
    cutoff = time.time() - HOURS_OLD_FOR_TEMP * 3600
    paths: list[Path] = []
    for profile in _user_profiles():
        for variable in ("TEMP", "TMP"):
            candidate = profile / "AppData" / "Local" / "Temp"
            if candidate.is_dir() and candidate not in paths:
                paths.append(candidate)

    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    system_temp = system_root / "Temp"
    if _is_admin() and system_temp.is_dir():
        paths.append(system_temp)

    reclaimed = deleted = 0
    for path in paths:
        r, d = _safe_delete_tree(path, cutoff)
        reclaimed += r
        deleted += d

    return MaintenanceResult(
        "Temporary files",
        "OK",
        f"Removed {deleted} stale temp files older than {HOURS_OLD_FOR_TEMP}h.",
        reclaimed,
        {"paths_checked": [str(p) for p in paths]},
    )


def clean_crash_dumps() -> MaintenanceResult:
    cutoff = time.time() - DAYS_OLD_FOR_DUMPS * 86400
    paths = [
        profile / "AppData" / "Local" / "CrashDumps"
        for profile in _user_profiles()
    ]
    system_root = Path(os.environ.get("SystemRoot", r"C:\Windows"))
    paths.append(system_root / "Minidump")

    reclaimed = deleted = 0
    for path in paths:
        r, d = _safe_delete_tree(path, cutoff)
        reclaimed += r
        deleted += d

    return MaintenanceResult(
        "Crash dump retention",
        "OK",
        f"Removed {deleted} crash/minidump files older than {DAYS_OLD_FOR_DUMPS} days.",
        reclaimed,
    )


def memory_health() -> MaintenanceResult:
    memory = psutil.virtual_memory()
    swap = psutil.swap_memory()
    pressure = "high" if memory.percent >= 90 else "normal"
    return MaintenanceResult(
        "Memory health",
        "WARNING" if pressure == "high" else "OK",
        (
            f"RAM usage {memory.percent:.1f}% "
            f"({memory.used / 1024**3:.1f}/{memory.total / 1024**3:.1f} GB); "
            f"pagefile/swap usage {swap.percent:.1f}%."
        ),
        details={
            "ram_percent": round(memory.percent, 1),
            "available_gb": round(memory.available / 1024**3, 2),
            "swap_percent": round(swap.percent, 1),
            "action": "observe_only",
        },
    )


def storage_health() -> MaintenanceResult:
    root = Path(os.environ.get("SystemDrive", "C:")) / os.sep
    usage = shutil.disk_usage(root)
    free_gb = usage.free / 1024**3
    used_percent = (usage.used / usage.total) * 100 if usage.total else 0
    status = "WARNING" if free_gb < 20 else "OK"
    return MaintenanceResult(
        "Storage health",
        status,
        f"System drive: {free_gb:.1f} GB free ({used_percent:.1f}% used).",
        details={
            "free_gb": round(free_gb, 2),
            "used_percent": round(used_percent, 1),
        },
    )


def hardware_health() -> MaintenanceResult:
    disks = []
    try:
        for disk in psutil.disk_partitions(all=False):
            if not disk.device:
                continue
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                disks.append({
                    "mountpoint": disk.mountpoint,
                    "free_gb": round(usage.free / 1024**3, 2),
                })
            except OSError:
                continue
    except Exception as exc:
        return MaintenanceResult("Drive inventory", "WARNING", str(exc))

    return MaintenanceResult(
        "Drive inventory",
        "OK",
        f"Checked {len(disks)} mounted volumes.",
        details={"volumes": disks},
    )


def run_daily_maintenance() -> list[MaintenanceResult]:
    """Run the daily suite. Each operation is isolated so one failure doesn't stop the rest."""
    operations = (
        clean_temp,
        clean_crash_dumps,
        memory_health,
        storage_health,
        hardware_health,
    )
    results: list[MaintenanceResult] = []
    for operation in operations:
        try:
            results.append(operation())
        except Exception as exc:
            results.append(MaintenanceResult(operation.__name__, "FAILED", str(exc)))

    _write_history(results)
    return results


def _write_history(results: list[MaintenanceResult]) -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "results": [asdict(result) for result in results],
    }
    with HISTORY_FILE.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def last_runs(limit: int = 7) -> list[dict]:
    if not HISTORY_FILE.is_file():
        return []
    lines = HISTORY_FILE.read_text(encoding="utf-8").splitlines()
    runs = []
    for line in lines[-limit:]:
        try:
            runs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return list(reversed(runs))
