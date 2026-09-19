from modules.developer_center import parsed_inventory

def test_parsed_inventory_accepts_object(monkeypatch):
    monkeypatch.setattr("modules.developer_center.inventory", lambda: '{"Features":[],"SSH":[]}')
    value=parsed_inventory()
    assert value["Features"] == []



def test_inventory_uses_valid_developer_mode_registry_path(monkeypatch):
    import base64
    import modules.developer_center as developer

    captured = {}

    class Result:
        returncode = 0
        stdout = "{}"
        stderr = ""

    def fake_command(exe, args=(), timeout=60):
        captured["args"] = args
        return Result()

    monkeypatch.setattr(developer, "_command", fake_command)
    developer.inventory()

    encoded = captured["args"][-1]
    script = base64.b64decode(encoded).decode("utf-16le")
    assert r"HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\AppModelUnlock" in script
