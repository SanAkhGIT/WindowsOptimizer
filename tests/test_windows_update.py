from modules.windows_update import reset_components


def test_reset_components_is_callable():
    assert callable(reset_components)
