import winreg

import tweaks.essential as essential


def test_consumer_policy_state_is_not_applied_by_default(monkeypatch):
    monkeypatch.setattr(
        essential,
        "_state",
        lambda root, path, name, desired: "NOT APPLIED",
    )
    assert essential._consumer_state() == "NOT APPLIED"


def test_activity_history_requires_both_policy_values(monkeypatch):
    values = {
        "PublishUserActivities": "APPLIED",
        "UploadUserActivities": "NOT APPLIED",
    }

    def fake_state(root, path, name, desired):
        return values[name]

    monkeypatch.setattr(essential, "_state", fake_state)
    assert essential._activity_state() == "NOT APPLIED"


def test_activity_history_detects_policy_conflict(monkeypatch):
    values = {
        "PublishUserActivities": "CONFLICT",
        "UploadUserActivities": "APPLIED",
    }

    monkeypatch.setattr(
        essential,
        "_state",
        lambda root, path, name, desired: values[name],
    )
    assert essential._activity_state() == "CONFLICT"
