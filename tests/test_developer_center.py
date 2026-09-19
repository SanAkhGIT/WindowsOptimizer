from modules.developer_center import parsed_inventory

def test_parsed_inventory_accepts_object(monkeypatch):
    monkeypatch.setattr("modules.developer_center.inventory", lambda: '{"Features":[],"SSH":[]}')
    value=parsed_inventory()
    assert value["Features"] == []
