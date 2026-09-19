from core.process import _decode_output


def test_decode_output_prefers_utf8():
    assert _decode_output("Verification 100% complete.".encode("utf-8")) == "Verification 100% complete."


def test_decode_output_handles_utf8_bom():
    assert _decode_output(b"\xef\xbb\xbfWindows repair complete.") == "Windows repair complete."
