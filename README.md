# Windows Optimizer

WindowsOptimizer is a Windows 11 optimization and maintenance suite built around:

**Discover → Review → Backup → Apply → Verify → Recover**

It is being designed as a long-lived local Windows utility rather than a collection of one-off registry scripts.

## What is implemented

- PySide6 desktop GUI with category-based operation views
- Windows build, CPU, GPU, RAM, disk and laptop/desktop discovery
- Administrator detection
- Registry snapshots before changes
- Windows System Restore point integration
- Operation execution and machine-readable logs
- Risk/reversibility/restart metadata for each operation
- Taskbar left alignment
- Transparency control
- Pure-black wallpaper
- Windows Game Mode control
- Optional Game DVR capture disable
- Advertising ID privacy control
- DNS maintenance
- Explorer restart repair action
- WinGet installed-software inventory
- Minimal / Standard / Gaming / Performance profiles
- Modular catalog architecture

## Design rules

1. Do not blindly apply every tweak.
2. Do not disable Defender, security software, Windows Update, core services or networking in default profiles.
3. Prefer supported Windows settings over undocumented registry hacks.
4. Every behavior-changing operation must explain its trade-off.
5. Performance claims should eventually be backed by measurements.
6. Debloat must be selective and reversible, not a destructive package purge.
7. The GUI is only a shell; Windows operations live in testable modules.

## Feature direction

The project takes feature inspiration from established utilities such as Chris Titus Tech's WinUtil and the archived Windows Powertool. WinUtil currently covers application installation, tweaks, fixes, updates and presets, while Windows Powertool documents optimization, debloat and restore workflows. WindowsOptimizer is intentionally implementing its own architecture rather than executing their remote scripts.

## Roadmap

### Phase 1 — Engine
- [x] System discovery
- [x] Operation catalog
- [x] Backup
- [x] Restore point
- [x] Apply executor
- [x] Operation logging
- [ ] Per-operation verification
- [ ] Per-operation rollback

### Phase 2 — Windows management
- [ ] Startup manager with impact analysis
- [ ] Services analyzer with safe recommendations
- [ ] Power-plan manager
- [ ] Network adapter analyzer
- [ ] Before/after latency and throughput checks
- [ ] Windows Update center
- [ ] Repair center: DISM, SFC, Store, Search, Update

### Phase 3 — Software
- [x] WinGet inventory
- [ ] Software install/update UI
- [ ] Software uninstall UI
- [ ] Curated application catalog
- [ ] Selective debloat
- [ ] Reinstall/restore paths for removable packages

### Phase 4 — Gaming
- [x] Game Mode
- [x] Optional Game DVR control
- [ ] Gaming profile based on detected hardware
- [ ] Background-process analysis
- [ ] Power/GPU/network recommendations
- [ ] Benchmark mode so changes can be measured

### Phase 5 — Profiles & automation
- [x] JSON profile foundation
- [ ] Import/export profiles
- [ ] Dry-run / preview mode
- [ ] Apply report
- [ ] Scheduled maintenance
- [ ] Offline-first operation
- [ ] Signed releases

## Run

PowerShell:
py -m pip install -r requirements.txt
py main.py

## Build

Run build.bat to produce the Windows executable.

The goal is a clean, explainable optimizer that can grow into a serious Windows management tool without turning into an unsafe "apply everything" script.
