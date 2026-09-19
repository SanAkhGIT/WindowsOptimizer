"""Review and staged application of WindowsOptimizer configurations."""

from dataclasses import dataclass

from core.configuration import validate
from modules.software import CATALOG


@dataclass(frozen=True)
class ConfigurationDiff:
    tweak_select: tuple
    tweak_clear: tuple
    apps_install: tuple
    apps_clear: tuple
    features_enable: tuple
    apps_unknown: tuple


def compare(data, current_tweaks, current_apps, enabled_features):
    validate(data)
    wanted_tweaks = set(data.get("tweaks", []))
    wanted_apps = set(data.get("apps", []))
    wanted_features = set(data.get("windows_features", []))
    known_apps = {app.id for app in CATALOG}
    current_tweaks = set(current_tweaks)
    current_apps = set(current_apps)
    enabled_features = set(enabled_features)
    return ConfigurationDiff(
        tuple(sorted(wanted_tweaks - current_tweaks)),
        tuple(sorted(current_tweaks - wanted_tweaks)),
        tuple(sorted((wanted_apps - current_apps) & known_apps)),
        tuple(sorted(current_apps - wanted_apps)),
        tuple(sorted(wanted_features - enabled_features)),
        tuple(sorted(wanted_apps - known_apps)),
    )


def summary(diff):
    return (
        f"Tweaks: +{len(diff.tweak_select)} / clear {len(diff.tweak_clear)}\n"
        f"Apps: +{len(diff.apps_install)} / clear {len(diff.apps_clear)}\n"
        f"Windows features to enable: +{len(diff.features_enable)}\n"
        f"Unknown catalog apps: {len(diff.apps_unknown)}"
    )


def feature_actions(diff, inventory):
    states = {item.name: item.state for item in inventory}
    actions = []
    for name in diff.features_enable:
        if name not in states:
            continue
        if states[name].lower() not in {"enabled", "installed"}:
            actions.append(name)
    return actions
