import json

import pytest

from modules import android_tv as tv


def test_target_serial_uses_fixed_classic_adb_port():
    assert tv.target_serial("192.168.0.21", 5555) == "192.168.0.21:5555"


def test_target_serial_brackets_ipv6_endpoint():
    assert tv.target_serial("fd00::21", 5555) == "[fd00::21]:5555"


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


def test_release_digest_verification():
    import hashlib

    data = b"official release payload"
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    assert tv.sha256_matches(data, digest)
    assert not tv.sha256_matches(data, "sha256:" + "0" * 64)
    assert not tv.sha256_matches(data, "md5:invalid")


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


def test_manual_tvhome_snapshot_normalizes_exact_prior_values():
    assert tv._normalize_manual_tvhome_preferences({
        "apps": ["org.smarttube.stable", "com.netflix.ninja"],
        "quick": ["Sound", "picture"],
    }) == {
        "apps": "org.smarttube.stable,com.netflix.ninja",
        "quick": "sound,picture",
    }


def test_manual_tvhome_snapshot_supports_auto_and_none():
    assert tv._normalize_manual_tvhome_preferences({"apps": "auto", "quick": "none"}) == {
        "apps": None,
        "quick": None,
    }


@pytest.mark.parametrize(
    "snapshot",
    [
        {"apps": ["com.netflix.ninja", "com.netflix.ninja"], "quick": []},
        {"apps": ["not a package"], "quick": []},
        {"apps": "auto", "quick": ["wifi"]},
        {"apps": "auto"},
    ],
)
def test_manual_tvhome_snapshot_rejects_invalid_values(snapshot):
    with pytest.raises(ValueError):
        tv._normalize_manual_tvhome_preferences(snapshot)


def test_read_journal_ignores_malformed_lines(monkeypatch, tmp_path):
    path = tmp_path / "changes.jsonl"
    path.write_text(
        '{"event":"change","id":"one"}\nnot-json\n{"event":"undo","change_id":"one"}\n',
        encoding="utf-8",
    )
    monkeypatch.setattr(tv, "journal_path", lambda: path)
    assert [item["event"] for item in tv.read_journal()] == ["change", "undo"]

def test_fizxix_home_component_is_supported():
    assert tv._tv_home_component(tv.FIZXIX_HOME_PACKAGE) == tv.FIZXIX_HOME_COMPONENT


def test_unknown_launcher_package_is_rejected():
    with pytest.raises(ValueError, match="Unsupported launcher package"):
        tv._tv_home_component("com.example.untrusted")


def test_fizxix_launcher_layout_command_targets_custom_package(monkeypatch):
    calls = []

    def fake_shell(adb, serial, *args, **kwargs):
        calls.append((adb, serial, args))
        return "Starting: Intent"

    monkeypatch.setattr(tv, "_shell", fake_shell)
    tv._set_tvhome_preferences(
        "adb.exe",
        "192.168.1.10:5555",
        {
            "apps": "com.netflix.ninja,org.videolan.vlc",
            "quick": "sound,picture",
            "launcher_package": tv.FIZXIX_HOME_PACKAGE,
        },
    )

    assert calls
    assert "-n" in calls[0][2]
    assert tv.FIZXIX_HOME_COMPONENT in calls[0][2]


def test_fizxix_installer_rejects_unexpected_filename_before_connect(tmp_path, monkeypatch):
    apk = tmp_path / "some-other.apk"
    apk.write_bytes(b"PK" + b"0" * 32)

    def forbidden_connect(*args, **kwargs):
        raise AssertionError("Must reject the wrong filename before attempting ADB connection.")

    monkeypatch.setattr(tv, "connect", forbidden_connect)
    with pytest.raises(ValueError, match="FIZXIX-TV-Detox.apk"):
        tv.install_fizxix_home(str(apk))



def test_half_speed_animation_settings_are_verified_and_reversible(monkeypatch):
    calls = []
    recorded = {}

    monkeypatch.setattr(tv, "connect", lambda *a, **k: {
        "serial": "192.168.1.10:5555", "adb_path": "adb.exe"
    })
    monkeypatch.setattr(tv, "_read_setting", lambda adb, serial, namespace, key: "1")
    def fake_put(adb, serial, namespace, key, value):
        calls.append((namespace, key, value))
    monkeypatch.setattr(tv, "_put_setting", fake_put)
    def fake_record(serial, kind, description, before, after):
        recorded.update({"serial": serial, "kind": kind, "before": before, "after": after})
    monkeypatch.setattr(tv, "_record_change", fake_record)

    result = tv.set_animation_scales_half("192.168.1.10", 5555, "adb.exe")

    assert len(calls) == 3
    assert all(value == "0.5" for _, _, value in calls)
    assert recorded["kind"] == "settings_batch"
    assert set(recorded["before"].values()) == {"1"}
    assert set(recorded["after"].values()) == {"0.5"}
    assert "saved for Undo" in result



@pytest.mark.parametrize(
    ("operation", "expected_key", "expected_value", "description_fragment"),
    [
        (lambda: tv.set_screensaver_enabled(True, "192.168.1.10", 5555, "adb.exe"),
         "secure.screensaver_enabled", "1", "Enable Android screensaver"),
        (lambda: tv.set_screensaver_enabled(False, "192.168.1.10", 5555, "adb.exe"),
         "secure.screensaver_enabled", "0", "Disable Android screensaver"),
        (lambda: tv.set_keep_screen_awake(True, "192.168.1.10", 5555, "adb.exe"),
         "global.stay_on_while_plugged_in", "3", "Keep screen awake"),
        (lambda: tv.set_keep_screen_awake(False, "192.168.1.10", 5555, "adb.exe"),
         "global.stay_on_while_plugged_in", "0", "Restore screen sleep"),
    ],
)
def test_display_options_preserve_prior_values_for_undo(
    monkeypatch, operation, expected_key, expected_value, description_fragment
):
    calls = []
    recorded = {}
    monkeypatch.setattr(tv, "connect", lambda *a, **k: {
        "serial": "192.168.1.10:5555", "adb_path": "adb.exe"
    })
    monkeypatch.setattr(tv, "_read_setting", lambda adb, serial, namespace, key: "previous-value")

    def fake_put(adb, serial, namespace, key, value):
        calls.append((namespace, key, value))

    def fake_record(serial, kind, description, before, after):
        recorded.update({
            "kind": kind, "description": description, "before": before, "after": after
        })

    monkeypatch.setattr(tv, "_put_setting", fake_put)
    monkeypatch.setattr(tv, "_record_change", fake_record)
    operation()

    assert len(calls) == 1
    namespace, key, value = calls[0]
    assert f"{namespace}.{key}" == expected_key
    assert value == expected_value
    assert recorded["kind"] == "settings_batch"
    assert recorded["before"][expected_key] == "previous-value"
    assert recorded["after"][expected_key] == expected_value
    assert description_fragment in recorded["description"]
