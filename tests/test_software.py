from modules.software import CATALOG, parse_upgrade_count


def test_catalog_ids_are_unique():
    ids = [row.id for row in CATALOG]
    assert len(ids) == len(set(ids))


def test_catalog_entries_are_complete():
    assert CATALOG
    for row in CATALOG:
        assert row.id and row.name and row.category


def test_parse_upgrade_count_footer():
    output = """
Name                 Id                         Version Available Source
-----------------------------------------------------------------------
PowerToys             Microsoft.PowerToys       0.1     0.2       winget
7-Zip                 7zip.7zip                 24.0    25.0      winget

2 upgrades available.
"""
    assert parse_upgrade_count(output) == 2


def test_parse_upgrade_count_no_updates():
    assert parse_upgrade_count("No applicable upgrade found.") == 0


def test_parse_upgrade_count_catalog_fallback():
    output = "Microsoft.PowerToys 0.1 0.2 winget\n7zip.7zip 24.0 25.0 winget"
    assert parse_upgrade_count(output) == 2


def test_parse_upgrade_count_ignores_unrelated_numbers():
    output = """
Some diagnostic text
10 seconds elapsed
No applicable upgrade found.
"""
    assert parse_upgrade_count(output) == 0


def test_update_report_scan_has_no_failures():
    from modules.software import UpdateReport

    report = UpdateReport(available=4, remaining=4, action="scan")
    assert report.attempted == 0
    assert report.updated == 0
    assert report.failed == 0
    assert not report.clean


def test_update_report_upgrade_failure_count_is_derived_from_attempted():
    from modules.software import UpdateReport

    report = UpdateReport(
        available=5,
        updated=3,
        remaining=2,
        attempted=5,
        action="upgrade",
    )
    assert report.failed == 2
    assert not report.clean
