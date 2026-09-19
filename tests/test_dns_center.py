from modules.dns_center import PRESETS

def test_dns_presets_are_known():
    assert PRESETS["Automatic (DHCP)"] is None
    assert PRESETS["Cloudflare"] == ["1.1.1.1", "1.0.0.1"]
