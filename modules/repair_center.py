from core.process import run_executable


def _run(executable, args, timeout=900):
    result = run_executable(executable, args, timeout=timeout)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or f"{executable} failed.")
    return result.stdout or f"{executable} completed successfully."


def component_store_check():
    return _run("DISM.exe", ("/Online", "/Cleanup-Image", "/CheckHealth"), 300)


def component_store_scan():
    return _run("DISM.exe", ("/Online", "/Cleanup-Image", "/ScanHealth"), 900)


def component_store_restore():
    return _run("DISM.exe", ("/Online", "/Cleanup-Image", "/RestoreHealth"), 1800)


def system_file_check():
    return _run("sfc.exe", ("/scannow",), 1800)


def win_update_reset():
    from modules.windows_update import reset_components
    return reset_components()
