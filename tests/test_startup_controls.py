import json
from modules import startup_controls

class FakeKey:
    def __init__(self): self.values={"Demo":("app.exe",1)}; self.deleted=[]
    def __enter__(self): return self
    def __exit__(self,*a): pass

def test_backup_path(monkeypatch,tmp_path):
    monkeypatch.setattr(startup_controls,"BACKUP_ROOT",tmp_path)
    assert startup_controls._load()=={}
    startup_controls._save({"Run:Demo":{"name":"Demo"}})
    assert startup_controls._load()["Run:Demo"]["name"]=="Demo"
