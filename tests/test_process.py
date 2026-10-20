import subprocess
import sys

from core.process import _decode_output, hidden_console_kwargs


def test_decode_output_prefers_utf8():
    assert _decode_output("Verification 100% complete.".encode("utf-8")) == "Verification 100% complete."


def test_decode_output_handles_utf8_bom():
    assert _decode_output(b"\xef\xbb\xbfWindows repair complete.") == "Windows repair complete."


def test_hidden_console_options_are_platform_safe():
    options = hidden_console_kwargs()
    if sys.platform == "win32":
        assert options["creationflags"] & subprocess.CREATE_NO_WINDOW
        startupinfo = options["startupinfo"]
        assert startupinfo.dwFlags & subprocess.STARTF_USESHOWWINDOW
        assert startupinfo.wShowWindow == subprocess.SW_HIDE
    else:
        assert options == {}
