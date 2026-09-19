from modules import startup

def test_startup_classification():
    item=startup.classify({"Name":"App","Location":"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run","User":"x","Command":"app.exe"})
    assert item["scope"]=="User"
    assert item["source"]=="Registry Run"
    assert item["executable"]=="app.exe"

def test_impact_stale():
    item={"source":"Registry Run","scope":"User","executable_exists":False,"executable":"missing.exe"}
    assert startup.impact(item)=="Stale/Unknown"

def test_impact_user():
    item={"source":"Registry Run","scope":"User","executable_exists":True,"executable":"C:\\Apps\\foo.exe"}
    assert startup.impact(item)=="User startup"
