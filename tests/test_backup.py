from core.backup import BackupManager


def test_backup_create_writes_manifest_without_registry_access(monkeypatch, tmp_path):
    manager = BackupManager(tmp_path)
    monkeypatch.setattr("core.backup._require_windows", lambda: None)
    monkeypatch.setattr("core.backup.CHECKS", ())

    path = manager.create()

    assert path.exists()
    assert (path / "registry_manifest.json").exists()
    assert (path / "registry_snapshot.json").exists()
    assert (path / "backup.json").exists()
