"""Named, versioned WindowsOptimizer profiles and operation planning.

Profiles are data only. Saving/loading a profile never changes Windows state.
User profiles live under %LOCALAPPDATA%\\WindowsOptimizer\\Profiles so they
remain separate from the read-only profiles shipped with the application.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import tempfile
from typing import Iterable

from core.configuration import SCHEMA_VERSION, validate
from core.configuration_engine import compare, ConfigurationDiff
from modules.software import CATALOG

PROFILE_SCHEMA_VERSION = 1
_PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{1,48}$")


def user_profile_dir() -> Path:
    root = os.environ.get("LOCALAPPDATA")
    base = Path(root) if root else Path.home() / "AppData" / "Local"
    return base / "WindowsOptimizer" / "Profiles"


@dataclass(frozen=True)
class Profile:
    id: str
    name: str
    description: str
    version: int
    created_utc: str
    updated_utc: str
    configuration: dict
    builtin: bool = False


@dataclass(frozen=True)
class PlanItem:
    kind: str
    action: str
    identifier: str
    reason: str


@dataclass(frozen=True)
class OperationPlan:
    profile_id: str
    profile_name: str
    items: tuple[PlanItem, ...]

    @property
    def count(self) -> int:
        return len(self.items)


def _normalise_id(value: str) -> str:
    value = str(value).strip().lower().replace(" ", "-")
    if not _PROFILE_ID.fullmatch(value):
        raise ValueError("Profile ID must be 2-49 characters: letters, numbers, '-' or '_'.")
    return value


def _profile_data(profile_id: str, name: str, description: str, configuration: dict,
                  *, version: int = 1, created_utc: str | None = None,
                  updated_utc: str | None = None, builtin: bool = False) -> dict:
    validate(configuration)
    now = datetime.now(timezone.utc).isoformat()
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "profile_id": _normalise_id(profile_id),
        "name": str(name).strip() or _normalise_id(profile_id).replace("-", " ").title(),
        "description": str(description).strip(),
        "version": int(version),
        "created_utc": created_utc or now,
        "updated_utc": updated_utc or now,
        "builtin": bool(builtin),
        "configuration_schema_version": SCHEMA_VERSION,
        "configuration": configuration,
    }


def _parse(data: dict, *, path: Path | None = None) -> Profile:
    if not isinstance(data, dict) or data.get("schema_version") != PROFILE_SCHEMA_VERSION:
        raise ValueError(f"Unsupported profile schema in {path or 'profile'}.")
    profile_id = _normalise_id(data.get("profile_id", ""))
    configuration = data.get("configuration")
    validate(configuration)
    return Profile(
        id=profile_id,
        name=str(data.get("name") or profile_id),
        description=str(data.get("description") or ""),
        version=int(data.get("version", 1)),
        created_utc=str(data.get("created_utc") or ""),
        updated_utc=str(data.get("updated_utc") or ""),
        configuration=configuration,
        builtin=bool(data.get("builtin", False)),
    )


def builtin_profiles() -> list[Profile]:
    root = Path(__file__).resolve().parent.parent / "profiles"
    result = []
    for path in sorted(root.glob("*.json")):
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            configuration = {
                "schema_version": SCHEMA_VERSION,
                "product": "WindowsOptimizer",
                "created_utc": datetime.now(timezone.utc).isoformat(),
                "tweaks": raw.get("tweaks", []),
                "apps": raw.get("apps", []),
                "windows_features": raw.get("windows_features", []),
                "power": raw.get("power", {}),
                "maintenance": raw.get("maintenance", {}),
            }
            result.append(_parse(_profile_data(
                path.stem, raw.get("name", path.stem), raw.get("description", ""),
                configuration, builtin=True,
            )))
        except (OSError, ValueError, json.JSONDecodeError):
            continue
    return result


def list_profiles() -> list[Profile]:
    result = builtin_profiles()
    directory = user_profile_dir()
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            try:
                result.append(_parse(json.loads(path.read_text(encoding="utf-8")), path=path))
            except (OSError, ValueError, json.JSONDecodeError):
                continue
    return sorted(result, key=lambda p: (not p.builtin, p.name.lower()))


def load_profile(profile_id: str) -> Profile:
    wanted = _normalise_id(profile_id)
    for profile in list_profiles():
        if profile.id == wanted:
            return profile
    raise KeyError(wanted)


def save_profile(profile_id: str, name: str, description: str, configuration: dict,
                 *, overwrite: bool = True) -> Profile:
    profile_id = _normalise_id(profile_id)
    directory = user_profile_dir()
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{profile_id}.json"
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    existing = None
    if path.exists():
        try:
            existing = _parse(json.loads(path.read_text(encoding="utf-8")), path=path)
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    data = _profile_data(
        profile_id,
        name,
        description,
        configuration,
        version=(existing.version + 1 if existing else 1),
        created_utc=(existing.created_utc if existing else None),
    )
    payload = json.dumps(data, indent=2, sort_keys=True) + "\n"
    fd, tmp_name = tempfile.mkstemp(prefix=f"{profile_id}.", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    finally:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
    return _parse(data, path=path)


def delete_profile(profile_id: str) -> None:
    profile = load_profile(profile_id)
    if profile.builtin:
        raise ValueError("Built-in profiles are read-only.")
    path = user_profile_dir() / f"{profile.id}.json"
    path.unlink(missing_ok=False)


def build_plan(profile: Profile | dict, current_tweaks: Iterable[str],
               current_apps: Iterable[str], enabled_features: Iterable[str]) -> OperationPlan:
    if isinstance(profile, dict):
        profile = _parse(profile)
    diff: ConfigurationDiff = compare(
        profile.configuration, current_tweaks, current_apps, enabled_features
    )
    items = []
    for value in diff.tweak_select:
        items.append(PlanItem("tweak", "enable", value, "Selected by profile and not currently selected."))
    for value in diff.apps_install:
        items.append(PlanItem("app", "install", value, "Selected by profile and not currently selected."))
    for value in diff.features_enable:
        items.append(PlanItem("windows_feature", "enable", value, "Requested by profile and not enabled."))
    for value in diff.apps_unknown:
        items.append(PlanItem("app", "skip", value, "Not present in the local application catalog."))
    return OperationPlan(profile.id, profile.name, tuple(items))


def format_plan(plan: OperationPlan) -> str:
    lines = [f"PROFILE PLAN — {plan.profile_name}", "", f"{plan.count} actionable item(s)"]
    for item in plan.items:
        prefix = "SKIP" if item.action == "skip" else item.action.upper()
        lines.append(f"{prefix:<6} {item.kind:<16} {item.identifier} — {item.reason}")
    if not plan.items:
        lines.append("No changes are required by the current additive profile.")
    return "\n".join(lines)
