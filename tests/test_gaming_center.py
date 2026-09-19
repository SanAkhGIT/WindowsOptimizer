from modules.gaming_center import parsed_inventory

def test_parsed_inventory_accepts_object(monkeypatch):
    monkeypatch.setattr("modules.gaming_center.inventory", lambda: '{"Gaming":{"GameMode":1}}')
    assert parsed_inventory()["Gaming"]["GameMode"] == 1

def test_parsed_inventory_rejects_non_object(monkeypatch):
    monkeypatch.setattr("modules.gaming_center.inventory", lambda: '[]')
    assert parsed_inventory() == {}



def test_inventory_uses_valid_registry_paths(monkeypatch):
    import modules.gaming_center as gaming

    captured = {}

    class Result:
        returncode = 0
        stdout = "{}"
        stderr = ""

    def fake_ps(script, timeout=90):
        captured["script"] = script
        return Result()

    monkeypatch.setattr(gaming, "_ps", fake_ps)
    gaming.inventory()

    script = captured["script"]
    assert r"HKCU:\Software\Microsoft\GameBar" in script
    assert r"HKCU:\Software\Microsoft\Windows\CurrentVersion\GameDVR" in script
    assert r"HKLM:\SYSTEM\CurrentControlSet\Control\GraphicsDrivers" in script
