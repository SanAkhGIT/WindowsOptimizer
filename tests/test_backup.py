import json

import core.backup as backup


def test_backup_create_with_empty_manifest(monkeypatch, tmp_path):
    monkeypatch.setattr(backup, "winreg", object())
    monkeypatch.setattr(backup, "CHECKS", ())

    path = backup.BackupManager(tmp_path).create()

    assert (path / "registry_manifest.json").exists()
    assert (path / "registry_snapshot.json").exists()
    payload = json.loads((path / "backup.json").read_text(encoding="utf-8"))
    assert payload["entry_count"] == 0
