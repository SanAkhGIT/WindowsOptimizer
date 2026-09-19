from modules.windows_features import _validate_name


def test_feature_names_reject_shell_metacharacters():
    for value in ("*", "Hyper-V;Write-Host x", "A|B", "A&B", "A?B"):
        try:
            _validate_name(value)
        except ValueError:
            pass
        else:
            raise AssertionError(value)


def test_feature_names_accept_exact_names():
    _validate_name("Microsoft-Windows-Subsystem-Linux")
    _validate_name("Hyper-V")
