from modules import hardware_monitor

class Fake:
    returncode=0
    stdout='[{"CurrentClockSpeed":4200,"LoadPercentage":25}]'
    stderr=''

def test_cpu_query(monkeypatch):
    monkeypatch.setattr(hardware_monitor,"run_executable",lambda *a,**k:Fake())
    assert "CurrentClockSpeed" in hardware_monitor.cpu()

def test_fan_and_temperature_queries_exist():
    assert callable(hardware_monitor.fans)
    assert callable(hardware_monitor.temperatures)
