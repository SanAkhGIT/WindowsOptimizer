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
