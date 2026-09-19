from pathlib import Path
import tempfile
from core.configuration import build,save,load,diff

def test_configuration_round_trip(tmp_path):
    path=tmp_path/"machine.json"
    data=build(["b","a"],["App.B"],["Feature-X"],"Balanced")
    save(path,data)
    assert load(path)["tweaks"] == ["a","b"]

def test_configuration_diff():
    data=build(["a","b"],["App.B"])
    result=diff(data,["a","c"],["App.C"])
    assert result["tweaks_to_select"] == ["b"]
    assert result["tweaks_to_clear"] == ["c"]
    assert result["apps_to_select"] == ["App.B"]
    assert result["apps_to_clear"] == ["App.C"]
