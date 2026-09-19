# Windows Optimizer

A Windows 11 post-install optimizer built around a safe scan/preview/apply workflow.

## Current foundation

- PySide6 GUI
- Windows/system information detection
- Administrator detection
- Registry backup snapshots
- Left taskbar alignment
- Transparency reduction
- Generated pure-black desktop and lock-screen assets
- Modular tweak architecture
- PyInstaller build support

## Safety model

The intended architecture is:

Scan -> Preview -> Backup -> Apply -> Verify -> Rollback

This repository is deliberately conservative at this stage. Each future Windows tweak should be individually tested and documented for supported Windows builds before being enabled by default.

## Run

```powershell
py -m pip install -r requirements.txt
py main.py
```

## Build

Run `build.bat` to create:

```text
dist\WindowsOptimizer.exe
```

## Development notes

See `docs/tweaks.md` for the tweak documentation requirements.
