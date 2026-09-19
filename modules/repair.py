from core.process import run_executable


def explorer():
    r = run_executable("taskkill", ["/f", "/im", "explorer.exe"], 30)
    if r.returncode not in (0, 128):
        raise RuntimeError(r.stderr or r.stdout)
    run_executable("explorer.exe", [], 30)
    return "Explorer restarted successfully."


def _clean_console_output(text):
    """Turn SFC/DISM progress streams into readable final-result text."""
    lines = []
    for raw in (text or "").replace("\r", "\n").splitlines():
        line = raw.strip()
        if not line:
            continue
        # SFC/DISM repeatedly redraw progress on the same console line.
        if "%" in line and (
            "complete" in line.lower()
            or "progress" in line.lower()
            or line.endswith("%")
        ):
            continue
        if line not in lines:
            lines.append(line)
    return "\n".join(lines)


def _repair_result(tool, result):
    output = _clean_console_output(result.stdout)
    if result.returncode:
        detail = _clean_console_output(result.stderr) or output
        raise RuntimeError(f"{tool} failed (exit code {result.returncode}).\n{detail}")
    return output or f"{tool} completed successfully."


def sfc():
    result = run_executable("sfc.exe", ["/scannow"], 1800)
    return _repair_result("SFC", result)


def dism():
    result = run_executable(
        "DISM.exe",
        ["/Online", "/Cleanup-Image", "/RestoreHealth"],
        1800,
    )
    return _repair_result("DISM", result)
