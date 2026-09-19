"""Portable Windows Optimizer configuration snapshots.

Import is intentionally review-first: loading a file changes only the current
GUI selections. It never applies tweaks, installs packages, changes features,
or changes power settings by itself.
"""

from datetime import datetime, timezone
import json
from pathlib import Path

SCHEMA_VERSION = 1


def build(tweak_ids, package_ids=(), features=(), power_plan=None, maintenance=None):
    return {
        "schema_version": SCHEMA_VERSION,
        "product": "WindowsOptimizer",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "tweaks": sorted(set(tweak_ids)),
        "apps": sorted(set(package_ids)),
        "windows_features": sorted(set(features)),
        "power": {"active_plan": power_plan} if power_plan else {},
        "maintenance": maintenance or {},
    }


def validate(data):
    if not isinstance(data, dict):
        raise ValueError("Configuration must be a JSON object.")
    if data.get("product") != "WindowsOptimizer":
        raise ValueError("This file is not a WindowsOptimizer configuration.")
    if data.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"Unsupported configuration schema: {data.get('schema_version')!r}")
    for key in ("tweaks", "apps", "windows_features"):
        if not isinstance(data.get(key, []), list) or not all(isinstance(v, str) for v in data.get(key, [])):
            raise ValueError(f"Configuration field '{key}' must be a list of strings.")
    return data


def save(path, data):
    path = Path(path)
    validate(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load(path):
    path = Path(path)
    data = json.loads(path.read_text(encoding="utf-8"))
    return validate(data)


def diff(data, tweak_ids, package_ids=()):
    validate(data)
    wanted_tweaks = set(data.get("tweaks", []))
    wanted_apps = set(data.get("apps", []))
    current_tweaks = set(tweak_ids)
    current_apps = set(package_ids)
    return {
        "tweaks_to_select": sorted(wanted_tweaks - current_tweaks),
        "tweaks_to_clear": sorted(current_tweaks - wanted_tweaks),
        "apps_to_select": sorted(wanted_apps - current_apps),
        "apps_to_clear": sorted(current_apps - wanted_apps),
    }
