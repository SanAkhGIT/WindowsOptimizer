from modules.catalog import all_tweaks

def test_catalog_has_unique_ids():
    tweaks=all_tweaks()
    ids=[t.id for t in tweaks]
    assert ids
    assert len(ids)==len(set(ids))

def test_catalog_operations_have_metadata():
    for tweak in all_tweaks():
        assert tweak.name
        assert tweak.category
        assert tweak.risk in {"SAFE","CAUTION","ADVANCED"}
        assert tweak.restart
