from core.configuration import build
from core.profile_manager import (
    Profile,
    build_plan,
    format_plan,
    save_profile,
    user_profile_dir,
)


def test_build_plan_is_additive():
    profile = Profile(
        "test-profile",
        "Test Profile",
        "",
        1,
        "",
        "",
        build(["a", "b"], ["Mozilla.Firefox", "missing"], ["Feature-X"]),
        False,
    )
    plan = build_plan(profile, ["a"], ["Google.Chrome"], [])
    assert [x.identifier for x in plan.items if x.action != "skip"] == ["b", "Mozilla.Firefox", "Feature-X"]
    assert any(x.action == "skip" and x.identifier == "missing" for x in plan.items)


def test_save_profile_increments_version(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    configuration = build(["a"])
    first = save_profile("my-profile", "My Profile", "test", configuration)
    second = save_profile("my-profile", "My Profile", "updated", configuration)
    assert first.version == 1
    assert second.version == 2
    assert second.description == "updated"
    assert (user_profile_dir() / "my-profile.json").exists()


def test_format_plan_contains_actions():
    profile = Profile("p1", "Profile One", "", 1, "", "", build(["a"]), False)
    text = format_plan(build_plan(profile, [], [], []))
    assert "ENABLE" in text
    assert "Profile One" in text
