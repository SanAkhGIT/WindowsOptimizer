import json

import pytest

from modules import android_tv as tv


def test_target_serial_uses_fixed_classic_adb_port():
    assert tv.target_serial("192.168.0.21", 5555) == "192.168.0.21:5555"


def test_target_serial_rejects_ip_with_appended_port():
    with pytest.raises(ValueError):
        tv.target_serial("192.168.0.21:5555", 5555)


def test_target_serial_validates_port():
    with pytest.raises(ValueError):
        tv.target_serial("192.168.0.21", 0)
    with pytest.raises(ValueError):
        tv.target_serial("192.168.0.21", 65536)


def test_package_list_parser_only_returns_package_names():
    assert tv.parse_package_list(
        "package:com.example.one\nnot-a-package\npackage:com.example.two\n"
    ) == {"com.example.one", "com.example.two"}


def test_meminfo_parser_does_not_merge_unrelated_digits():
    parsed = tv.parse_meminfo(
        "MemTotal:        1966100 kB\n"
        "MemFree:           84560 kB\n"
        "MemAvailable:     786104 kB\n"
        "Buffers:             9844 kB\n"
        "SwapTotal:         489472 kB\n"
        "SwapFree:           92672 kB\n"
    )
    assert parsed == {
        "MemTotal": 1966100,
        "MemFree": 84560,
        "MemAvailable": 786104,
        "SwapTotal": 489472,
        "SwapFree": 92672,
    }


@pytest.mark.parametrize(
    "package",
    [
        "com.android.vending",
        "com.google.android.gms",
        "com.google.android.gsf",
        "com.android.tv.settings",
        "com.android.systemui",
        "com.mft.rcupair",
        "com.droidlogic.android.tv",
        "com.sdt.ota",
        "com.sdt.upgrade",
        "com.google.android.tv.dfuservice",
        "com.example.keyboardhelper",
    ],
)
def test_protected_packages_are_never_debloat_candidates(package):
    assert tv.is_protected_package(package)


def test_package_disable_rejects_unreviewed_package_before_adb():
    with pytest.raises(ValueError, match="reviewed optional-package allowlist"):
        tv.disable_package("com.google.android.gms")


def test_home_launchers_are_not_in_optional_debloat_allowlist():
    assert tv.GOOGLE_TV_LAUNCHER not in tv.DEBLOAT_CANDIDATES
    assert tv.GOOGLE_TV_SETUP not in tv.DEBLOAT_CANDIDATES
    assert tv.TV_DETOX_PACKAGE not in tv.DEBLOAT_CANDIDATES


def test_tv_detox_preferences_parser():
    xml = (
        '<?xml version="1.0" encoding="utf-8" standalone="yes" ?>'
        '<map><string name="apps">com.netflix.ninja,org.smarttube.stable</string>'
        '<string name="quick">sound,picture</string></map>'
    )
    assert tv._parse_tvhome_preferences(xml) == {
        "apps": "com.netflix.ninja,org.smarttube.stable",
        "quick": "sound,picture",
    }


def test_tv_detox_preferences_missing_values_use_auto_defaults():
    assert tv._parse_tvhome_preferences("<map />") == {"apps": None, "quick": None}


def test_read_journal_ignores_malformed_lines(monkeypatch, tmp_path):
    path = tmp_path / "changes.jsonl"
    path.write_text(
        '{"event":"change","id":"one"}\nnot-json\n{"event":"undo","change_id":"one"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(tv, "journal_path", lambda: path)
    assert [item["event"] for item in tv.read_journal()] == ["change", "undo"]
