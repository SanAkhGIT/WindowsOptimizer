import modules.maintenance as maintenance


def test_daily_maintenance_contains_safe_operations():
    operations = [
        maintenance.clean_temp,
        maintenance.clean_crash_dumps,
        maintenance.memory_health,
        maintenance.storage_health,
        maintenance.hardware_health,
    ]
    assert all(callable(operation) for operation in operations)


def test_temp_cleanup_does_not_follow_symlinks(tmp_path):
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    try:
        link.symlink_to(target, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    reclaimed, deleted = maintenance._safe_delete_tree(tmp_path, 10**20)
    assert reclaimed == 0
    assert deleted == 0
