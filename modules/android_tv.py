"""Conservative Android TV management over ADB.

All package and setting mutations are explicit, verified, and recorded in a local
JSONL journal. This module never uninstalls packages and never disables unknown or
platform-critical packages. It does not require ADB to be on PATH.
"""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import json
import os
import re
import shutil
import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from core.process import run_executable


TV_DETOX_PACKAGE = "com.ansub.tvhome"
TV_DETOX_COMPONENT = "com.ansub.tvhome/.MainActivity"
GOOGLE_TV_LAUNCHER = "com.google.android.apps.tv.launcherx"
GOOGLE_TV_SETUP = "com.google.android.tungsten.setupwraith"
GOOGLE_TV_LAUNCHERS = (
    GOOGLE_TV_LAUNCHER,
    "com.google.android.tvlauncher",
    "com.google.android.leanbacklauncher",
)
SETUP_PACKAGES = (GOOGLE_TV_SETUP,)
TV_DETOX_RELEASE_API = "https://api.github.com/repos/Ansub/tv-detox/releases/latest"

# These are review candidates, never automatically selected. The target device must
# actually contain the package, and the user confirms every individual operation.
DEBLOAT_CANDIDATES = {
    "com.android.dreams.basic": "AOSP basic screensaver provider. Disabling may remove a fallback screensaver.",
    "com.google.android.apps.tv.dreamx": "Google TV screensaver/ambient experience. Disabling removes its features.",
    "com.android.printspooler": "Android print service; unnecessary only if you never print from the TV.",
    "com.android.htmlviewer": "Basic HTML viewer; a few apps may rely on it to display local HTML.",
    "com.google.android.feedback": "Google feedback reporter; disabling removes feedback/reporting entry points.",
    "com.google.android.play.games": "Google Play Games services/UI; keep enabled if you play games that use it.",
    "com.android.adservices.api": "Android advertising services; effects vary by Android build and apps.",
    "com.android.ondevicepersonalization.services": "On-device personalization service; recommendations/ads may change.",
    "com.android.federatedcompute.services": "Federated-compute component; feature use varies by firmware.",
    "com.android.healthconnect.controller": "Health Connect UI/controller; keep if any app uses Health Connect.",
    "com.android.health.connect.backuprestore": "Health Connect backup/restore component; keep if Health Connect is used.",
}
# Exact and prefix deny-lists are defense in depth. Changes are also allow-listed above.
PROTECTED_PACKAGES = {
    "com.android.vending", "com.google.android.gms", "com.google.android.gsf",
    "com.android.inputmethod.latin", "com.google.android.inputmethod.latin",
    "com.android.systemui", "com.android.settings", "com.android.tv.settings",
    "com.android.permissioncontroller", "com.google.android.permissioncontroller",
    "com.android.webview", "com.google.android.webview", "com.google.android.tts",
    "com.google.android.katniss", "com.mft.rcupair",
    "com.sdt.ota", "com.sdt.upgrade", "com.google.android.tv.dfuservice",
}
PROTECTED_PREFIXES = ("com.droidlogic.", "com.sdt.")
APP_PACKAGES_TO_CHECK = (
    "org.smarttube.stable",
    "com.jio.media.jiotvplus",
    "com.graymatrix.did",
    "com.stremio.one",
    "com.spotify.tv.android",
    "org.videolan.vlc",
    "com.netflix.ninja",
    "com.amazon.amazonvideo.livingroom",
)
ANIMATION_SETTINGS = (
    ("global", "window_animation_scale"),
    ("global", "transition_animation_scale"),
    ("global", "animator_duration_scale"),
)
_COMPONENT_RE = re.compile(r"^([A-Za-z0-9_.]+)/([A-Za-z0-9_.$]+)$")


def is_protected_package(package: str) -> bool:
    """Return whether a package is explicitly protected from package mutations."""
    if package in PROTECTED_PACKAGES:
        return True
    if package.startswith(PROTECTED_PREFIXES):
        return True
    lowered = package.lower()
    if any(token in lowered for token in ("inputmethod", "keyboard", "bluetooth", "systemui")):
        return True
    if any(token in lowered for token in ("permissioncontroller", "webview", "katniss", "rcupair")):
        return True
    return False


def parse_package_list(output: str) -> set[str]:
    """Parse pm list packages output into a set of package names."""
    return {
        line.strip()[8:].strip()
        for line in (output or "").splitlines()
        if line.strip().startswith("package:") and line.strip()[8:].strip()
    }


def parse_meminfo(output: str) -> dict[str, int]:
    """Parse Android /proc/meminfo values in kB without mixing unrelated numbers."""
    values: dict[str, int] = {}
    for line in (output or "").splitlines():
        match = re.match(r"^\s*(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree):\s*(\d+)\s+kB\b", line)
        if match:
            values[match.group(1)] = int(match.group(2))
    return values


def _adb_path(preferred: str | None = None) -> str:
    if preferred:
        candidate = Path(os.path.expandvars(os.path.expanduser(preferred)))
        if candidate.is_file() and candidate.name.lower() in ("adb.exe", "adb"):
            return str(candidate)
        raise RuntimeError(f"ADB executable not found at: {preferred}")

    located = shutil.which("adb.exe") or shutil.which("adb")
    if located:
        return located

    roots = []
    local_app_data = os.environ.get("LOCALAPPDATA")
    user_profile = os.environ.get("USERPROFILE") or str(Path.home())
    if local_app_data:
        roots.append(Path(local_app_data) / "Android" / "Sdk" / "platform-tools" / "adb.exe")
    roots.extend((
        Path(user_profile) / "AppData" / "Local" / "Android" / "Sdk" / "platform-tools" / "adb.exe",
        Path(user_profile) / "platform-tools" / "adb.exe",
        Path(user_profile) / "Downloads" / "platform-tools" / "adb.exe",
        Path("C:/Android/platform-tools/adb.exe"),
    ))
    for candidate in roots:
        if candidate.is_file():
            return str(candidate)
    raise RuntimeError("adb.exe was not found. Install Google Android SDK Platform-Tools or browse to adb.exe.")


def target_serial(tv_ip: str, port: int = 5555) -> str:
    try:
        parsed_ip = ipaddress.ip_address((tv_ip or "").strip())
    except ValueError as exc:
        raise ValueError("Enter the TV's IPv4/IPv6 address, not an ADB command or port.") from exc
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("ADB port must be between 1 and 65535.")
    ip = f"[{parsed_ip}]" if parsed_ip.version == 6 else str(parsed_ip)
    return f"{ip}:{port}"


def _run_adb(adb: str, args, timeout: int = 30, check: bool = True) -> str:
    result = run_executable(adb, tuple(str(item) for item in args), timeout)
    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    if check and result.returncode != 0:
        raise RuntimeError(output or f"ADB command failed (exit code {result.returncode}).")
    return output


def _shell(adb: str, serial: str, *args, timeout: int = 30, check: bool = True) -> str:
    return _run_adb(adb, ("-s", serial, "shell", *args), timeout=timeout, check=check)


def connect(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> dict:
    """Connect to a classic ADB TCP endpoint and verify the device state."""
    adb = _adb_path(adb_path)
    serial = target_serial(tv_ip, port)
    connect_output = _run_adb(adb, ("connect", serial), timeout=20, check=False)
    state = _run_adb(adb, ("-s", serial, "get-state"), timeout=20, check=False).strip()
    if state != "device":
        detail = state or connect_output or "No device state returned."
        raise RuntimeError(f"ADB did not reach the device state 'device' for {serial}: {detail}")
    return {"adb_path": adb, "serial": serial, "connect_output": connect_output, "state": state}


def _require_device(adb_path: str | None, serial: str) -> str:
    adb = _adb_path(adb_path)
    state = _run_adb(adb, ("-s", serial, "get-state"), timeout=15, check=False).strip()
    if state != "device":
        raise RuntimeError(f"{serial} is not ready (ADB state: {state or 'unavailable'}). Connect and authorize the TV first.")
    return adb


def _read_setting(adb: str, serial: str, namespace: str, key: str) -> str:
    return _shell(adb, serial, "settings", "get", namespace, key, check=False).strip()


def _put_setting(adb: str, serial: str, namespace: str, key: str, value: str | None) -> None:
    if value is None or value == "null":
        _shell(adb, serial, "settings", "delete", namespace, key)
    else:
        _shell(adb, serial, "settings", "put", namespace, key, value)
    observed = _read_setting(adb, serial, namespace, key)
    expected = "null" if value is None or value == "null" else value
    if observed != expected:
        raise RuntimeError(
            f"Android did not retain {namespace}.{key}: expected {expected!r}, got {observed!r}."
        )


def _package_sets(adb: str, serial: str) -> tuple[set[str], set[str], set[str]]:
    all_packages = parse_package_list(_shell(adb, serial, "pm", "list", "packages", check=False))
    enabled = parse_package_list(_shell(adb, serial, "pm", "list", "packages", "-e", check=False))
    disabled = parse_package_list(_shell(adb, serial, "pm", "list", "packages", "-d", check=False))
    return all_packages, enabled, disabled


def _component_from_output(output: str) -> str | None:
    for line in reversed((output or "").splitlines()):
        value = line.strip()
        if value.startswith("priority=") or value.startswith("No activity found"):
            continue
        if _COMPONENT_RE.match(value):
            return value
    return None


def _home_component(adb: str, serial: str) -> str | None:
    output = _shell(
        adb, serial, "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME",
        check=False,
    )
    return _component_from_output(output)


def _current_home_raw(adb: str, serial: str) -> str:
    return _shell(
        adb, serial, "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME",
        check=False,
    )


def _is_disabled(adb: str, serial: str, package: str) -> bool:
    return package in parse_package_list(_shell(adb, serial, "pm", "list", "packages", "-d", check=False))


def _record_change(serial: str, kind: str, description: str, before, after, reversible: bool = True) -> str:
    record_id = uuid.uuid4().hex
    record = {
        "event": "change",
        "id": record_id,
        "utc": datetime.now(timezone.utc).isoformat(),
        "target": serial,
        "kind": kind,
        "description": description,
        "before": before,
        "after": after,
        "reversible": bool(reversible),
        "inverse": _inverse_description(kind, before) if reversible else None,
    }
    path = journal_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return record_id


def _inverse_description(kind: str, before) -> str:
    if kind == "package_disabled":
        return "pm enable --user 0 <package>"
    if kind == "package_enabled":
        return "pm disable-user --user 0 <package> (only if it was disabled before)"
    if kind == "settings_batch":
        return "Restore exact previous Android setting values, including unset values"
    if kind == "tvhome_config":
        return "Restore the prior tv-detox app/shortcut configuration"
    if kind == "tvhome_home":
        return f"Restore previous HOME component: {before.get('home') or 'unavailable'}"
    if kind == "google_home":
        return "Restore previous HOME; re-disable the Google TV launcher if it was disabled before"
    return "No automatic inverse is defined"


def journal_path() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    root = Path(base) if base else Path.home() / ".local" / "share"
    return root / "WindowsOptimizer" / "android-tv" / "changes.jsonl"


def read_journal() -> list[dict]:
    path = journal_path()
    if not path.is_file():
        return []
    records = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            value = json.loads(line)
            if isinstance(value, dict):
                records.append(value)
        except json.JSONDecodeError:
            continue
    return records


def package_candidates(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> list[dict]:
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    installed, enabled, disabled = _package_sets(adb, serial)
    rows = []
    for package, description in DEBLOAT_CANDIDATES.items():
        if package not in installed or is_protected_package(package):
            continue
        rows.append({
            "package": package,
            "description": description,
            "state": "disabled" if package in disabled else ("enabled" if package in enabled else "unknown"),
            "selected": False,
        })
    return rows


def disable_package(package: str, tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    if package not in DEBLOAT_CANDIDATES or is_protected_package(package):
        raise ValueError(f"{package!r} is not in the reviewed optional-package allowlist.")
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    installed, enabled, disabled = _package_sets(adb, serial)
    if package not in installed:
        raise RuntimeError(f"{package} is not installed on {serial}.")
    if package in disabled:
        return f"{package} was already disabled; no change made."
    if package not in enabled:
        raise RuntimeError(f"Could not confirm that {package} is enabled; no change made.")
    _shell(adb, serial, "pm", "disable-user", "--user", "0", package)
    if not _is_disabled(adb, serial, package):
        raise RuntimeError(f"Android did not confirm that {package} is disabled.")
    _record_change(serial, "package_disabled", f"Disable optional package {package}", {"enabled": True}, {"enabled": False, "package": package})
    return f"Disabled {package}. Undo is recorded locally."


def enable_package(package: str, tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    if package not in DEBLOAT_CANDIDATES or is_protected_package(package):
        raise ValueError(f"{package!r} is not in the reviewed optional-package allowlist.")
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    installed, enabled, disabled = _package_sets(adb, serial)
    if package not in installed:
        raise RuntimeError(f"{package} is not installed on {serial}.")
    if package not in disabled:
        return f"{package} is not disabled; no change made."
    _shell(adb, serial, "pm", "enable", "--user", "0", package)
    _, enabled_after, disabled_after = _package_sets(adb, serial)
    if package not in enabled_after or package in disabled_after:
        raise RuntimeError(f"Android did not confirm that {package} is enabled.")
    _record_change(serial, "package_enabled", f"Re-enable optional package {package}", {"enabled": False}, {"enabled": True, "package": package})
    return f"Enabled {package}. The previous disabled state is recorded for undo."


def health_check(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> dict:
    """Read-only health scan. It never enables/disables packages or changes settings."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    prop_names = {
        "manufacturer": "ro.product.manufacturer",
        "model": "ro.product.model",
        "device": "ro.product.device",
        "android_version": "ro.build.version.release",
        "sdk": "ro.build.version.sdk",
    }
    properties = {
        label: _shell(adb, serial, "getprop", prop, check=False).strip()
        for label, prop in prop_names.items()
    }
    raw_mem = _shell(adb, serial, "cat", "/proc/meminfo", check=False)
    mem_kb = parse_meminfo(raw_mem)
    _, enabled, disabled = _package_sets(adb, serial)
    launcher_state = {}
    for package in (TV_DETOX_PACKAGE, *GOOGLE_TV_LAUNCHERS, *SETUP_PACKAGES):
        launcher_state[package] = (
            "disabled" if package in disabled else
            "enabled" if package in enabled else "not installed or unknown"
        )
    apps = {}
    for package in APP_PACKAGES_TO_CHECK:
        if package not in enabled and package not in disabled:
            apps[package] = {"installed": False, "background_appop": "not installed for user 0", "standby_bucket": "not available"}
            continue
        apps[package] = {
            "installed": True,
            "background_appop": _shell(adb, serial, "cmd", "appops", "get", package, "RUN_IN_BACKGROUND", check=False).strip(),
            "standby_bucket": _shell(adb, serial, "am", "get-standby-bucket", package, check=False).strip(),
        }
    settings = {
        "private_dns_mode": _read_setting(adb, serial, "global", "private_dns_mode"),
        "private_dns_specifier": _read_setting(adb, serial, "global", "private_dns_specifier"),
        "window_animation_scale": _read_setting(adb, serial, "global", "window_animation_scale"),
        "transition_animation_scale": _read_setting(adb, serial, "global", "transition_animation_scale"),
        "animator_duration_scale": _read_setting(adb, serial, "global", "animator_duration_scale"),
        "screensaver_enabled": _read_setting(adb, serial, "secure", "screensaver_enabled"),
        "screensaver_components": _read_setting(adb, serial, "secure", "screensaver_components"),
    }
    managed = []
    changes = read_journal()
    undone_ids = {item.get("change_id") for item in changes if item.get("event") == "undo"}
    recent_changes = []
    for item in changes:
        if item.get("event") != "change" or item.get("target") != serial:
            continue
        if item.get("kind") in ("package_disabled", "package_enabled") and item.get("id") not in undone_ids:
            managed.append(item)
        recent_changes.append({
            "utc": item.get("utc"),
            "description": item.get("description"),
            "kind": item.get("kind"),
            "reversible": item.get("reversible", False),
            "inverse": item.get("inverse"),
            "status": "undone" if item.get("id") in undone_ids else "pending",
        })
    return {
        "connection": {"serial": serial, "state": connection["state"], "connect_output": connection["connect_output"]},
        "device": properties,
        "home": {"raw": _current_home_raw(adb, serial), "component": _home_component(adb, serial)},
        "launchers_and_setup": launcher_state,
        "disabled_packages": sorted(disabled),
        "memory_kb": mem_kb,
        "memory_mib": {key: round(value / 1024, 1) for key, value in mem_kb.items()},
        "settings": settings,
        "background_restrictions": apps,
        "windows_optimizer_changes": managed,
        "recent_changes": recent_changes[-25:],
        "journal_path": str(journal_path()),
    }


def set_animation_scales_zero(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    before = {f"{namespace}.{key}": _read_setting(adb, serial, namespace, key) for namespace, key in ANIMATION_SETTINGS}
    applied = []
    try:
        for namespace, key in ANIMATION_SETTINGS:
            _put_setting(adb, serial, namespace, key, "0")
            applied.append((namespace, key))
    except Exception:
        for namespace, key in reversed(applied):
            try:
                _put_setting(adb, serial, namespace, key, before[f"{namespace}.{key}"])
            except Exception:
                pass
        raise
    _record_change(serial, "settings_batch", "Set animation scales to zero", before, {f"{namespace}.{key}": "0" for namespace, key in ANIMATION_SETTINGS})
    return "Animation scales set to 0 and verified. Exact previous values are saved for Undo."


def disable_screensaver(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    before = {"secure.screensaver_enabled": _read_setting(adb, serial, "secure", "screensaver_enabled")}
    _put_setting(adb, serial, "secure", "screensaver_enabled", "0")
    _record_change(serial, "settings_batch", "Disable Android screensaver setting", before, {"secure.screensaver_enabled": "0"})
    return "Android screensaver setting disabled and verified. Exact previous value is saved for Undo."


def _parse_tvhome_preferences(xml_text: str) -> dict:
    """Read config.xml only if the app permits run-as; never guess the old layout."""
    root = ET.fromstring(xml_text)
    result = {"apps": None, "quick": None}
    for element in root.iter():
        name = element.attrib.get("name")
        if name in result:
            result[name] = element.text or ""
    return result


def _read_tvhome_preferences(adb: str, serial: str) -> dict:
    output = _shell(adb, serial, "run-as", TV_DETOX_PACKAGE, "cat", "shared_prefs/config.xml", check=False)
    if not output or "not debuggable" in output.lower() or "permission denied" in output.lower() or "unknown package" in output.lower():
        raise RuntimeError(
            "Exact tv-detox layout backup is unavailable (the installed app may not allow run-as). "
            "For safety, tile/shortcut changes are blocked rather than overwriting an unknown layout. "
            "Edit app tiles directly on the TV by holding OK on a tile."
        )
    try:
        return _parse_tvhome_preferences(output)
    except ET.ParseError as exc:
        raise RuntimeError("Could not parse tv-detox's saved layout; no layout change was made.") from exc


def tv_launchable_apps(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> list[str]:
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    output = _shell(
        adb, serial, "cmd", "package", "query-activities", "--brief",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LEANBACK_LAUNCHER",
        check=False,
    )
    packages = set()
    for line in output.splitlines():
        component = _component_from_output(line.strip())
        if component:
            package = component.split("/", 1)[0]
            if package != TV_DETOX_PACKAGE and package not in PROTECTED_PACKAGES:
                packages.add(package)
    return sorted(packages, key=str.casefold)


def tv_detox_layout(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> dict:
    """Return the exact saved app/shortcut preferences or fail closed if unreadable."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    _, enabled, _ = _package_sets(adb, serial)
    if TV_DETOX_PACKAGE not in enabled:
        raise RuntimeError("tv-detox is not installed and enabled on this device.")
    return _read_tvhome_preferences(adb, serial)


def _set_tvhome_preferences(adb: str, serial: str, preferences: dict) -> None:
    apps = preferences.get("apps") or "auto"
    quick = preferences.get("quick") or "none"
    output = _shell(
        adb, serial, "am", "start", "-n", TV_DETOX_COMPONENT,
        "--es", "apps", apps,
        "--es", "quick", quick,
        "--es", "stamp", uuid.uuid4().hex,
        check=False,
    )
    if "error:" in output.lower() or "exception" in output.lower():
        raise RuntimeError(f"tv-detox could not apply its saved configuration: {output}")


def configure_tv_detox(
    apps: list[str] | None = None,
    quick_shortcuts: list[str] | None = None,
    tv_ip: str = "192.168.0.21",
    port: int = 5555,
    adb_path: str | None = None,
) -> str:
    """Customize tv-detox only when the prior configuration can be backed up exactly."""
    allowed_quick = {"bluetooth", "sound", "picture"}
    quick = list(dict.fromkeys((quick_shortcuts or [])))
    if any(item not in allowed_quick for item in quick):
        raise ValueError("Allowed tv-detox shortcuts are bluetooth, sound, and picture.")
    selected_apps = None if apps is None else list(dict.fromkeys(apps))
    if selected_apps is not None and len(selected_apps) > 48:
        raise ValueError("Select no more than 48 TV apps.")
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    _, enabled, _ = _package_sets(adb, serial)
    if TV_DETOX_PACKAGE not in enabled:
        raise RuntimeError("tv-detox is not confirmed enabled. Install or enable it before changing its layout.")
    before = _read_tvhome_preferences(adb, serial)
    if selected_apps is not None:
        launchable = set(tv_launchable_apps(tv_ip, port, adb))
        invalid = sorted(set(selected_apps) - launchable)
        if invalid:
            raise ValueError(f"These packages are not launchable TV apps on this device: {', '.join(invalid)}")
    apps_value = (before.get("apps") or "auto") if selected_apps is None else (",".join(selected_apps) if selected_apps else "auto")
    quick_value = (before.get("quick") or "none") if quick_shortcuts is None else (",".join(quick) if quick else "none")
    stamp = uuid.uuid4().hex
    output = _shell(
        adb, serial, "am", "start", "-n", TV_DETOX_COMPONENT,
        "--es", "apps", apps_value,
        "--es", "quick", quick_value,
        "--es", "stamp", stamp,
        check=False,
    )
    if "error:" in output.lower() or "exception" in output.lower():
        raise RuntimeError(f"tv-detox did not accept the layout update: {output}")
    after = dict(before)
    if selected_apps is not None:
        after["apps"] = selected_apps or None
    if quick_shortcuts is not None:
        after["quick"] = quick or None
    _record_change(
        serial, "tvhome_config", "Customize tv-detox app tiles and shortcuts",
        before, after,
    )
    return "tv-detox layout updated. Previous app/shortcut preferences were backed up for exact Undo."


def _set_home_component(adb: str, serial: str, component: str) -> None:
    match = _COMPONENT_RE.match(component)
    if not match:
        raise ValueError(f"Not a valid Android component: {component!r}")
    package = match.group(1)
    _shell(adb, serial, "cmd", "role", "add-role-holder", "--user", "0", "android.app.role.HOME", package, check=False)
    _shell(adb, serial, "cmd", "package", "set-home-activity", component, check=False)
    actual = _home_component(adb, serial)
    if actual != component and not (actual and actual.startswith(package + "/")):
        raise RuntimeError(f"Home switch did not verify. Requested {component}; Android now resolves {actual or 'no Home activity'}.")


def set_tv_detox_home(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    _, enabled, _ = _package_sets(adb, serial)
    if TV_DETOX_PACKAGE not in enabled:
        raise RuntimeError("tv-detox is not installed and enabled. Install/enable it first; no Home change was made.")
    previous = _home_component(adb, serial)
    if not previous:
        raise RuntimeError("Android did not resolve the current Home activity; refusing to change Home.")
    try:
        _set_home_component(adb, serial, TV_DETOX_COMPONENT)
    except Exception as exc:
        try:
            _set_home_component(adb, serial, previous)
        except Exception as rollback_exc:
            raise RuntimeError(f"Home switch failed ({exc}) and automatic rollback also failed ({rollback_exc}). Emergency command: adb -s {serial} shell pm enable {GOOGLE_TV_LAUNCHER}") from exc
        raise RuntimeError(f"Home switch failed and the previous Home was restored: {exc}") from exc
    _record_change(serial, "tvhome_home", "Set tv-detox as Android Home", {"home": previous}, {"home": TV_DETOX_COMPONENT})
    return f"tv-detox is now Home ({TV_DETOX_COMPONENT}). Existing launchers were not disabled."


def _google_launcher_component(adb: str, serial: str) -> str | None:
    output = _shell(
        adb, serial, "cmd", "package", "query-activities", "--brief",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.HOME",
        check=False,
    )
    for line in output.splitlines():
        component = _component_from_output(line.strip())
        if component and component.startswith(GOOGLE_TV_LAUNCHER + "/"):
            return component
    fallback = _shell(
        adb, serial, "cmd", "package", "resolve-activity", "--brief",
        "-a", "android.intent.action.MAIN", "-c", "android.intent.category.LEANBACK_LAUNCHER",
        GOOGLE_TV_LAUNCHER, check=False,
    )
    for line in fallback.splitlines():
        component = _component_from_output(line.strip())
        if component and component.startswith(GOOGLE_TV_LAUNCHER + "/"):
            return component
    return None


def restore_google_tv_home(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    """Restore the stock launcher without uninstalling tv-detox or touching setup/TV-framework packages."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    installed, enabled, disabled = _package_sets(adb, serial)
    if GOOGLE_TV_LAUNCHER not in installed:
        raise RuntimeError(f"{GOOGLE_TV_LAUNCHER} is not installed; stock Home cannot be restored this way.")
    previous_home = _home_component(adb, serial)
    if not previous_home:
        raise RuntimeError("Android did not resolve the current Home activity; refusing to switch Home.")
    was_disabled = GOOGLE_TV_LAUNCHER in disabled
    if was_disabled:
        _shell(adb, serial, "pm", "enable", "--user", "0", GOOGLE_TV_LAUNCHER)
    _, enabled_after, disabled_after = _package_sets(adb, serial)
    if GOOGLE_TV_LAUNCHER not in enabled_after or GOOGLE_TV_LAUNCHER in disabled_after:
        if was_disabled:
            raise RuntimeError("Google TV launcher could not be enabled; tv-detox remains unchanged.")
        raise RuntimeError("Google TV launcher is not confirmed enabled; Home was not changed.")
    component = _google_launcher_component(adb, serial)
    if not component:
        if was_disabled:
            _shell(adb, serial, "pm", "disable-user", "--user", "0", GOOGLE_TV_LAUNCHER, check=False)
        raise RuntimeError("No Home/Leanback activity was found for Google TV Launcher. Previous Home remains active.")
    try:
        _set_home_component(adb, serial, component)
        actual = _home_component(adb, serial)
        if not actual or not actual.startswith(GOOGLE_TV_LAUNCHER + "/"):
            raise RuntimeError(f"Google TV Home verification failed (current={actual}).")
    except Exception as exc:
        rollback_error = None
        try:
            _set_home_component(adb, serial, previous_home)
        except Exception as rollback_exc:
            rollback_error = rollback_exc
        # Never disable the newly enabled stock launcher if restoring the previous Home failed:
        # leaving it available is safer than risking no usable HOME activity.
        if was_disabled and rollback_error is None:
            _shell(adb, serial, "pm", "disable-user", "--user", "0", GOOGLE_TV_LAUNCHER, check=False)
        if rollback_error is not None:
            raise RuntimeError(
                f"Google TV Home failed ({exc}); restoring previous Home also failed ({rollback_error}). "
                f"The stock launcher was left enabled as a recovery path. Emergency command: "
                f"adb -s {serial} shell pm enable {GOOGLE_TV_LAUNCHER}"
            ) from exc
        raise RuntimeError(f"Google TV Home failed; previous Home restored: {exc}") from exc
    _record_change(
        serial, "google_home", "Restore Google TV Launcher as Home",
        {"home": previous_home, "launcher_was_disabled": was_disabled},
        {"home": component, "launcher_enabled": True},
    )
    return f"Google TV Launcher is now Home ({component}). tv-detox remains installed; setup packages were not changed."


def open_tv_settings(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    connection = connect(tv_ip, port, adb_path)
    output = _shell(
        connection["adb_path"], connection["serial"], "am", "start",
        "-a", "android.settings.SETTINGS", check=False,
    )
    if "error:" in output.lower() or "exception" in output.lower():
        raise RuntimeError(f"Android Settings could not be opened: {output}")
    return "Requested Android Settings to open. This action does not change any setting."


def install_or_update_tv_detox(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    """Download the official release over HTTPS and install/replace in place; never uninstall."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / ".local" / "share"))
    folder = base / "WindowsOptimizer" / "android-tv"
    folder.mkdir(parents=True, exist_ok=True)
    apk_path = folder / "tvhome.apk"
    headers = {"User-Agent": "WindowsOptimizer Android TV module", "Accept": "application/vnd.github+json"}
    try:
        with urlopen(Request(TV_DETOX_RELEASE_API, headers=headers), timeout=30) as response:
            release = json.loads(response.read(2 * 1024 * 1024).decode("utf-8"))
        asset = next((item for item in release.get("assets", []) if item.get("name") == "tvhome.apk"), None)
        if not asset:
            raise RuntimeError("The latest GitHub release does not expose a tvhome.apk asset.")
        asset_url = asset.get("browser_download_url", "")
        parsed_url = urlparse(asset_url)
        if parsed_url.scheme != "https" or parsed_url.netloc.lower() != "github.com" or "/releases/download/" not in parsed_url.path:
            raise RuntimeError("The release asset URL is not an approved HTTPS GitHub release URL.")
        expected_digest = asset.get("digest")
        if not expected_digest or not expected_digest.startswith("sha256:"):
            raise RuntimeError("GitHub did not publish a SHA-256 digest for tvhome.apk; refusing an unverifiable install.")
        with urlopen(Request(asset_url, headers={"User-Agent": "WindowsOptimizer Android TV module"}), timeout=90) as response:
            apk = response.read(80 * 1024 * 1024 + 1)
    except Exception as exc:
        raise RuntimeError(f"Could not verify/download the official tv-detox release: {exc}") from exc
    if len(apk) < 25_000 or len(apk) > 80 * 1024 * 1024 or not apk.startswith(b"PK"):
        raise RuntimeError("Downloaded file did not pass basic APK/ZIP sanity checks; it was not installed.")
    expected_hex = expected_digest.split(":", 1)[1].strip().lower()
    actual_hex = hashlib.sha256(apk).hexdigest()
    if len(expected_hex) != 64 or not hmac.compare_digest(actual_hex, expected_hex):
        raise RuntimeError("Downloaded tvhome.apk SHA-256 does not match the GitHub release digest; it was not installed.")
    apk_path.write_bytes(apk)
    result = _run_adb(adb, ("-s", serial, "install", "-r", str(apk_path)), timeout=180, check=False)
    if "success" not in result.lower():
        raise RuntimeError(
            "tv-detox install/update failed. Nothing was uninstalled. If Android reports "
            "UPDATE_INCOMPATIBLE, the APK signing key differs; do not uninstall automatically. "
            f"ADB said: {result}"
        )
    installed, enabled, disabled = _package_sets(adb, serial)
    if TV_DETOX_PACKAGE not in installed:
        raise RuntimeError("APK installer reported success, but package verification failed.")
    if TV_DETOX_PACKAGE in disabled:
        return f"Official tv-detox was installed/updated for {serial}, but remains disabled as before. Enable it explicitly before setting it as Home. No package was uninstalled."
    return f"Installed/updated official tv-detox for {serial}. APK cached at {apk_path}. No package was uninstalled."


def run_cache_trim(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    """Maintenance action with no inverse; the UI must explain that limitation."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    output = _shell(adb, serial, "pm", "trim-caches", "512M", timeout=180, check=False)
    _record_change(serial, "irreversible", "Trim Android package caches to free up to 512 MB", None, {"output": output}, reversible=False)
    return f"Cache trim command completed (its returned output may be empty):\n{output or '(no output)'}\nNo undo exists for cache trimming."


def compile_apps_speed_profile(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    """Optional and firmware-dependent ART compilation; it has no simple inverse."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    output = _shell(
        adb, serial, "cmd", "package", "compile", "-m", "speed-profile", "-a",
        timeout=600, check=False,
    )
    if "unknown command" in output.lower() or "error:" in output.lower() or "exception" in output.lower():
        raise RuntimeError(f"Package compilation failed or is unsupported on this firmware: {output}")
    _record_change(serial, "irreversible", "ART speed-profile compilation for installed packages", None, {"output": output}, reversible=False)
    return f"Compilation command completed. Results depend on firmware and app profiles:\n{output or '(no output)'}\nNo exact inverse exists for ART recompilation."


def undo_last_change(tv_ip: str = "192.168.0.21", port: int = 5555, adb_path: str | None = None) -> str:
    """Undo the newest un-undone recorded change for this device, in reverse order."""
    connection = connect(tv_ip, port, adb_path)
    serial, adb = connection["serial"], connection["adb_path"]
    records = read_journal()
    undone = {item.get("change_id") for item in records if item.get("event") == "undo"}
    pending = [
        item for item in records
        if item.get("event") == "change" and item.get("target") == serial and item.get("id") not in undone
    ]
    if not pending:
        return "No pending WindowsOptimizer TV changes are recorded for this device."
    reversible = [item for item in pending if item.get("reversible", False)]
    if not reversible:
        names = ", ".join(item.get("description", item.get("kind", "operation")) for item in pending[-3:])
        return f"No automatic inverse exists for the pending TV operations: {names}. No device setting was changed."
    latest = reversible[-1]
    newer_without_inverse = [
        item.get("description", item.get("kind", "operation"))
        for item in pending[pending.index(latest) + 1:]
        if not item.get("reversible", False)
    ]
    kind, before = latest.get("kind"), latest.get("before") or {}
    if kind == "package_disabled":
        package = latest.get("after", {}).get("package")
        if not package or package not in DEBLOAT_CANDIDATES:
            raise RuntimeError("Journal package is not on the reviewed optional-package allowlist; refusing to undo it.")
        if _is_disabled(adb, serial, package):
            _shell(adb, serial, "pm", "enable", "--user", "0", package)
            if _is_disabled(adb, serial, package):
                raise RuntimeError(f"Undo failed: {package} remains disabled.")
    elif kind == "package_enabled":
        package = latest.get("after", {}).get("package")
        if not package or package not in DEBLOAT_CANDIDATES:
            raise RuntimeError("Journal package is not on the reviewed optional-package allowlist; refusing to undo it.")
        if not _is_disabled(adb, serial, package):
            _shell(adb, serial, "pm", "disable-user", "--user", "0", package)
            if not _is_disabled(adb, serial, package):
                raise RuntimeError(f"Undo failed: {package} did not return to disabled state.")
    elif kind == "settings_batch":
        for setting, value in before.items():
            namespace, key = setting.split(".", 1)
            _put_setting(adb, serial, namespace, key, value)
    elif kind == "tvhome_config":
        _set_tvhome_preferences(adb, serial, before)
    elif kind == "tvhome_home":
        previous = before.get("home")
        if not previous:
            raise RuntimeError("Prior HOME component was not recorded; refusing an unsafe guess.")
        _set_home_component(adb, serial, previous)
    elif kind == "google_home":
        previous = before.get("home")
        if not previous:
            raise RuntimeError("Prior HOME component was not recorded; refusing an unsafe guess.")
        _set_home_component(adb, serial, previous)
        if before.get("launcher_was_disabled"):
            _shell(adb, serial, "pm", "disable-user", "--user", "0", GOOGLE_TV_LAUNCHER)
            if not _is_disabled(adb, serial, GOOGLE_TV_LAUNCHER):
                raise RuntimeError("Home was restored, but the launcher did not return to its previous disabled state.")
    else:
        raise RuntimeError(f"No inverse handler exists for journal change kind {kind!r}.")
    with journal_path().open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({
            "event": "undo", "change_id": latest["id"], "target": serial,
            "utc": datetime.now(timezone.utc).isoformat(),
        }) + "\n")
    message = f"Undid the latest reversible change: {latest.get('description', kind)}"
    if newer_without_inverse:
        message += "\nNewer operations left untouched because they have no inverse: " + "; ".join(newer_without_inverse)
    return message
