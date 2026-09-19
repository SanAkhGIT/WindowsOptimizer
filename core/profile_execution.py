"""Execute an explicitly approved profile plan.

The executor is intentionally additive: it only executes plan items that the
caller selected. It creates one backup for the approved batch and records a
per-item receipt after verification.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from core.backup import BackupManager
from core.operation_receipts import ReceiptItem, complete, new_receipt, save
from core.verification import verify_tweak
from modules.software import CATALOG, install, installed
from modules.windows_features import inventory as feature_inventory, set_feature
from modules.catalog import all_tweaks


@dataclass(frozen=True)
class ProfileExecutionResult:
    receipt_path: str
    backup_path: str | None
    status: str
    items: tuple[ReceiptItem, ...]


def _tweak_map():
    return {tweak.id: tweak for tweak in all_tweaks()}


def _feature_enabled(name: str) -> bool:
    return any(item.name == name and "Enabled" in item.state for item in feature_inventory())


def execute_approved_plan(profile, items, *, backup_manager=None, receipt_root=None):
    """Execute only the supplied approved plan items.

    A single registry backup is created before the first mutation. Empty plans
    are rejected so an approval action can never silently become a no-op.
    """
    items = tuple(items)
    if not items:
        raise ValueError("No approved operations were supplied.")

    backup_manager = backup_manager or BackupManager()
    backup_path = backup_manager.create()
    receipt = new_receipt(
        "profile",
        profile.id,
        profile.version,
        backup_path,
    )
    tweak_map = _tweak_map()
    catalog = {app.id: app for app in CATALOG}
    receipt_items = []

    for item in items:
        started = datetime.now().isoformat(timespec="seconds")
        try:
            if item.kind == "tweak" and item.action == "enable":
                tweak = tweak_map.get(item.identifier)
                if tweak is None or not tweak.apply:
                    raise ValueError(f"Unknown or non-actionable tweak: {item.identifier}")
                message = tweak.apply()
                verified, verification = verify_tweak(tweak)
                status = "VERIFIED" if verified is True else (
                    "APPLIED" if verified is None else "UNVERIFIED"
                )
                rollback_keys = tuple(tweak.metadata.get("rollback_keys", ()))
                rollback_supported = bool(tweak.rollback) or bool(backup_path and rollback_keys and tweak.check)
            elif item.kind == "app" and item.action == "install":
                if item.identifier not in catalog:
                    raise ValueError(f"Unknown catalog application: {item.identifier}")
                message = install(item.identifier)
                verified = installed(item.identifier, catalog[item.identifier].source)
                verification = (
                    "Verified installed state."
                    if verified
                    else "Install completed but WinGet did not report the package as installed."
                )
                status = "VERIFIED" if verified else "UNVERIFIED"
                rollback_supported = False
            elif item.kind == "windows_feature" and item.action == "enable":
                message = set_feature(item.identifier, True)
                verified = _feature_enabled(item.identifier)
                verification = (
                    "Verified Windows feature is enabled."
                    if verified
                    else "Enable completed but inventory did not report the feature as enabled."
                )
                status = "VERIFIED" if verified else "UNVERIFIED"
                rollback_supported = True
            else:
                raise ValueError(
                    f"Unsupported approved operation: {item.kind}/{item.action}"
                )
        except Exception as exc:
            message = str(exc)
            verification = f"Operation failed after start at {started}."
            status = "FAILED"
            rollback_supported = False

        receipt_items.append(
            ReceiptItem(
                item.kind,
                item.identifier,
                item.action,
                status,
                message,
                verification,
                rollback_supported,
                rollback_keys if item.kind == "tweak" else (),
            )
        )

    finished = complete(receipt, receipt_items)
    path = save(finished, receipt_root)
    return ProfileExecutionResult(
        str(path),
        str(backup_path) if backup_path else None,
        finished.status,
        tuple(receipt_items),
    )
