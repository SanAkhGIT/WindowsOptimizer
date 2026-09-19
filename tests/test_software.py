from modules.software import CATALOG

def test_catalog_ids_are_unique():
    ids=[row[0] for row in CATALOG]
    assert len(ids)==len(set(ids))

def test_catalog_entries_are_complete():
    assert CATALOG
    for package_id,name,category in CATALOG:
        assert package_id and name and category
