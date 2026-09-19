from modules.power_center import PLANS

def test_power_plan_aliases_are_supported():
    assert PLANS["Balanced"] == "SCHEME_BALANCED"
    assert PLANS["High performance"] == "SCHEME_MIN"
