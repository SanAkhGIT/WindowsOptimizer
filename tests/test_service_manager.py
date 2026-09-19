from modules.service_manager import _valid

def test_service_names_reject_command_separators():
    assert not _valid("bad;service")
    assert not _valid("bad|service")
    assert not _valid("bad\nservice")

def test_service_name_accepts_normal_name():
    assert _valid("Windows Update")
