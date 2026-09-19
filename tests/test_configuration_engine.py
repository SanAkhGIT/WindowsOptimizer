from core.configuration import build
from core.configuration_engine import compare, summary

def test_configuration_diff_is_additive():
    data=build(["a","b"],["Mozilla.Firefox","missing"],["Feature-X"])
    diff=compare(data,["a"],["Google.Chrome"],[])
    assert diff.tweak_select == ("b",)
    assert diff.tweak_clear == ()
    assert diff.apps_install == ("Mozilla.Firefox",)
    assert diff.apps_unknown == ("missing",)
    assert diff.features_enable == ("Feature-X",)

def test_summary_reports_counts():
    data=build(["a"],["Mozilla.Firefox"])
    diff=compare(data,[],[])
    text=summary(diff)
    assert "Tweaks: +1" in text
    assert "Apps: +1" in text
