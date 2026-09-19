from modules.startup_manager import classify

def test_classify_marks_user_run_as_manageable():
    item = classify({
        "Name": "Example",
        "Command": "C:\\Apps\\example.exe",
        "Location": r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run",
        "User": "TEST\\user",
    })
    assert item["source"] == "Registry Run"
    assert item["scope"] == "User"
    assert item["manageable"] is True

def test_classify_marks_system_run_read_only():
    item = classify({
        "Name": "Example",
        "Command": "C:\\Windows\\example.exe",
        "Location": r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
        "User": "",
    })
    assert item["manageable"] is False



def test_hklm_entry_remains_system_even_when_user_field_is_populated():
    item = classify({
        "Name": "MachineEntry",
        "Command": r"C:\Program Files\Vendor\app.exe",
        "Location": r"HKLM\Software\Microsoft\Windows\CurrentVersion\Run",
        "User": r"TEST\user",
    })
    assert item["scope"] == "System"
    assert item["manageable"] is False
