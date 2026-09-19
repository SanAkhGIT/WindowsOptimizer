import winreg
from core.logging import get_logger

logger = get_logger("registry")

def read_value(root, path, name):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_READ) as key:
            return winreg.QueryValueEx(key, name)
    except FileNotFoundError:
        return None

def write_dword(root, path, name, value):
    with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))
    logger.info("Registry changed | root=%s | key=%s | value=%s | type=DWORD | new_value=%r", root, path, name, int(value))

def write_string(root, path, name, value):
    with winreg.CreateKeyEx(root, path, 0, winreg.KEY_SET_VALUE) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, str(value))
    logger.info("Registry changed | root=%s | key=%s | value=%s | type=STRING | new_value=%r", root, path, name, str(value))

def delete_value(root, path, name):
    try:
        with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.DeleteValue(key, name)
        logger.info("Registry value deleted | root=%s | key=%s | value=%s", root, path, name)
    except FileNotFoundError:
        logger.info("Registry value already absent | root=%s | key=%s | value=%s", root, path, name)
