"""Persistent execution plans and receipts.

Receipts are append-only JSON records describing what WindowsOptimizer was
asked to do, what was attempted, and what verification reported.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import uuid


RECEIPT_VERSION = 1


def receipt_dir(root=None) -> Path:
    path = Path(root or (Path.home() / "WindowsOptimizerBackups")) / "receipts"
    path.mkdir(parents=True, exist_ok=True)
    return path


@dataclass(frozen=True)
class ReceiptItem:
    kind: str
    identifier: str
    action: str
    status: str
    message: str = ""
    verification: str = ""
    rollback_supported: bool = False
    rollback_keys: tuple[dict, ...] = ()


@dataclass(frozen=True)
class ExecutionReceipt:
    receipt_id: str
    created_utc: str
    source: str
    profile_id: str | None
    profile_version: int | None
    backup_path: str | None
    status: str
    items: tuple[ReceiptItem, ...]


def new_receipt(source, profile_id=None, profile_version=None, backup_path=None):
    return ExecutionReceipt(
        receipt_id=uuid.uuid4().hex,
        created_utc=datetime.now(timezone.utc).isoformat(),
        source=source,
        profile_id=profile_id,
        profile_version=profile_version,
        backup_path=str(backup_path) if backup_path else None,
        status="PLANNED",
        items=(),
    )


def complete(receipt, items):
    items = tuple(items)
    if any(item.status in {"FAILED", "ROLLBACK_FAILED"} for item in items):
        status = "FAILED"
    elif any(item.status in {"UNVERIFIED", "APPLIED"} for item in items):
        status = "COMPLETED_WITH_WARNINGS"
    else:
        status = "VERIFIED"
    return ExecutionReceipt(
        receipt.receipt_id, receipt.created_utc, receipt.source,
        receipt.profile_id, receipt.profile_version, receipt.backup_path,
        status, items,
    )


def save(receipt, root=None) -> Path:
    path = receipt_dir(root) / f"{receipt.created_utc.replace(':', '-')}_{receipt.receipt_id}.json"
    payload = {"receipt_version": RECEIPT_VERSION, **asdict(receipt)}
    payload["items"] = [asdict(item) for item in receipt.items]
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    return path


def load(path) -> ExecutionReceipt:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("receipt_version") != RECEIPT_VERSION:
        raise ValueError("Unsupported receipt version.")
    return ExecutionReceipt(
        data["receipt_id"], data["created_utc"], data["source"],
        data.get("profile_id"), data.get("profile_version"),
        data.get("backup_path"), data["status"],
        tuple(ReceiptItem(**item) for item in data.get("items", [])),
    )


def recent(root=None, limit=20):
    paths = sorted(receipt_dir(root).glob("*.json"), reverse=True)[:max(1, int(limit))]
    result = []
    for path in paths:
        try:
            result.append((path, load(path)))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return result
