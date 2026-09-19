"""Managed Microsoft Edge extension installation support."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BrowserExtension:
    id: str
    name: str
    version: str
    description: str
    browser: str = "Microsoft Edge"
    requires_developer_mode: bool = True
    source_url: str = "https://github.com/Pickle-Pixel/netflix-force-4k"


CATALOG = (
    BrowserExtension(
        id="netflix-force-4k",
        name="Netflix 4K",
        version="1.2.0",
        description=(
            "Unpacked Edge extension that adjusts Netflix capability detection "
            "for compatible Windows/Edge systems."
        ),
    ),
)


def catalog() -> tuple[BrowserExtension, ...]:
    return CATALOG


def _resource_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "extensions"
    return Path(__file__).resolve().parent.parent / "extensions"


def _install_root() -> Path:
    return (
        Path(os.environ.get("LOCALAPPDATA", Path.home()))
        / "WindowsOptimizer"
        / "BrowserExtensions"
    )


def _source_path(extension_id: str) -> Path:
    if extension_id not in {item.id for item in CATALOG}:
        raise ValueError(f"Unknown browser extension: {extension_id}")
    path = _resource_root() / extension_id
    manifest = path / "manifest.json"
    if not path.is_dir() or not manifest.is_file():
        raise FileNotFoundError(f"Bundled extension is missing: {path}")
    return path


def _validate_extension(source: Path) -> dict:
    try:
        manifest = json.loads((source / "manifest.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Invalid extension manifest: {exc}") from exc

    if manifest.get("manifest_version") != 3:
        raise RuntimeError("Only Manifest V3 extensions are supported.")
    if not manifest.get("name") or not manifest.get("version"):
        raise RuntimeError("Extension manifest is missing name or version.")
    return manifest


def manifest(extension_id: str = "netflix-force-4k") -> dict:
    return _validate_extension(_source_path(extension_id))


def installed_path(extension_id: str = "netflix-force-4k") -> Path:
    return _install_root() / extension_id


def installation_status(extension_id: str = "netflix-force-4k") -> dict:
    path = installed_path(extension_id)
    manifest_path = path / "manifest.json"
    if not manifest_path.is_file():
        return {"installed": False, "path": str(path), "version": None}

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"installed": False, "path": str(path), "version": None}

    return {
        "installed": True,
        "path": str(path),
        "version": manifest.get("version"),
        "name": manifest.get("name"),
    }


def install(extension_id: str = "netflix-force-4k") -> str:
    source = _source_path(extension_id)
    _validate_extension(source)

    destination = installed_path(extension_id)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(f"{destination.name}.staging")

    if staging.exists():
        shutil.rmtree(staging, ignore_errors=True)

    try:
        shutil.copytree(
            source,
            staging,
            ignore=shutil.ignore_patterns("__pycache__", ".git", "_metadata"),
        )
        if destination.exists():
            shutil.rmtree(destination)
        staging.replace(destination)
    except Exception:
        shutil.rmtree(staging, ignore_errors=True)
        raise

    return str(destination)


def remove(extension_id: str = "netflix-force-4k") -> str:
    path = installed_path(extension_id)
    if path.exists():
        shutil.rmtree(path)
        return f"Removed managed extension files: {path}"
    return f"No managed extension files found: {path}"


def _find_edge() -> str | None:
    roots = (
        os.environ.get("ProgramFiles(x86)", ""),
        os.environ.get("ProgramFiles", ""),
        os.environ.get("LOCALAPPDATA", ""),
    )
    relative = Path("Microsoft/Edge/Application/msedge.exe")
    for root in roots:
        if root:
            candidate = Path(root) / relative
            if candidate.is_file():
                return str(candidate)
    return shutil.which("msedge.exe")


def open_edge_extensions() -> str:
    edge = _find_edge()
    if edge:
        subprocess.Popen([edge, "edge://extensions/"], close_fds=True)
        return "Opened Microsoft Edge extension management."
    try:
        os.startfile("msedge://extensions/")  # type: ignore[attr-defined]
        return "Opened Microsoft Edge extension management."
    except OSError as exc:
        raise RuntimeError(
            "Microsoft Edge was not found. Open edge://extensions/ manually."
        ) from exc


def open_install_folder(extension_id: str = "netflix-force-4k") -> str:
    path = installed_path(extension_id)
    if not path.is_dir():
        raise FileNotFoundError("Install the extension first.")
    os.startfile(str(path))  # type: ignore[attr-defined]
    return str(path)
