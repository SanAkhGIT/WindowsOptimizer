from modules.appx import AppxPackage


def test_framework_and_non_removable_packages_are_protected():
    framework = AppxPackage(
        "Framework", "Framework_1.0_x64__test", "1.0", "CN=Test",
        "C:\\WindowsApps\\Framework", True, False, "System", "Ok"
    )
    non_removable = AppxPackage(
        "SystemApp", "SystemApp_1.0_x64__test", "1.0", "CN=Test",
        "C:\\WindowsApps\\SystemApp", False, True, "System", "Ok"
    )
    assert not framework.removable
    assert not non_removable.removable


def test_recommendation_is_only_a_hint_for_removable_packages():
    package = AppxPackage(
        "Microsoft.BingWeather", "Microsoft.BingWeather_1.0_x64__test",
        "1.0", "CN=Microsoft", "C:\\WindowsApps\\BingWeather",
        False, False, "System", "Ok"
    )
    assert package.removable
    assert package.recommended


def test_protected_store_is_never_recommended():
    package = AppxPackage(
        "Microsoft.WindowsStore", "Microsoft.WindowsStore_1.0_x64__test",
        "1.0", "CN=Microsoft", "C:\\WindowsApps\\Store",
        False, False, "System", "Ok"
    )
    assert not package.removable
    assert not package.recommended
