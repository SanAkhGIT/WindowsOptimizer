from modules.gaming_center import parsed_inventory

def test_parsed_inventory_accepts_object(monkeypatch):
    monkeypatch.setattr("modules.gaming_center.inventory", lambda: '{"Gaming":{"GameMode":1}}')
    assert parsed_inventory()["Gaming"]["GameMode"] == 1

def test_parsed_inventory_rejects_non_object(monkeypatch):
    monkeypatch.setattr("modules.gaming_center.inventory", lambda: '[]')
    assert parsed_inventory() == {}
