from modules import startup, power, network_center

class Fake:
    def __init__(self, returncode=0, stdout="ok", stderr=""):
        self.returncode=returncode; self.stdout=stdout; self.stderr=stderr

def test_startup_inventory_uses_powershell(monkeypatch):
    calls=[]
    monkeypatch.setattr(startup,"run_executable",lambda *args,**kwargs:(calls.append((args,kwargs)) or Fake(stdout="[]")))
    assert startup.inventory()=="[]"
    assert calls[0][0][0]=="powershell.exe"

def test_power_current(monkeypatch):
    monkeypatch.setattr(power,"run_executable",lambda *args,**kwargs:Fake(stdout="active"))
    assert power.current()=="active"

def test_power_failure(monkeypatch):
    monkeypatch.setattr(power,"run_executable",lambda *args,**kwargs:Fake(returncode=1,stderr="failed"))
    try:
        power.current()
        assert False
    except RuntimeError as exc:
        assert "failed" in str(exc)

def test_network_latency(monkeypatch):
    monkeypatch.setattr(network_center,"run_executable",lambda *args,**kwargs:Fake(stdout="ping output"))
    assert network_center.latency()=="ping output"
