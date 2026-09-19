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
