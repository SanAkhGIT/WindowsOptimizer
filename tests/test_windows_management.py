from modules import startup, power, network_center, services

class Fake:
    def __init__(self, returncode=0, stdout="ok", stderr=""):
        self.returncode=returncode; self.stdout=stdout; self.stderr=stderr

def test_startup_records_and_classification(monkeypatch):
    monkeypatch.setattr(startup,"run_executable",lambda *a,**k:Fake(stdout='[{"Name":"One","Location":"HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run","User":"x","Command":"app.exe"}]'))
    records=startup.records()
    assert len(records)==1
    assert startup.classify(records[0])["scope"]=="User"
    assert startup.classify(records[0])["source"]=="Registry Run"

def test_power_current(monkeypatch):
    monkeypatch.setattr(power,"run_executable",lambda *a,**k:Fake(stdout="active"))
    assert power.current()=="active"

def test_power_failure(monkeypatch):
    monkeypatch.setattr(power,"run_executable",lambda *a,**k:Fake(returncode=1,stderr="failed"))
    try:
        power.current()
        assert False
    except RuntimeError as exc:
        assert "failed" in str(exc)

def test_network_latency(monkeypatch):
    monkeypatch.setattr(network_center,"run_executable",lambda *a,**k:Fake(stdout="ping output"))
    assert network_center.latency()=="ping output"

def test_service_classification():
    assert services.classify({"DisplayName":"Windows Update","PathName":"C:\\Windows\\System32\\svchost.exe"})=="Windows"
    assert services.classify({"DisplayName":"NVIDIA Container","PathName":"C:\\Program Files\\NVIDIA\\x.exe"})=="Hardware/OEM"
    assert services.classify({"DisplayName":"Example Vendor","PathName":"C:\\Program Files\\Example\\x.exe"})=="Third-party/Unknown"
