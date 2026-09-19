from modules.service_manager import _valid

def test_service_names_reject_shell_separators():
    assert not _valid("bad;service")
    assert not _valid("bad|service")
    assert _valid("Windows Update")
