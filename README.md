# Windows Optimizer

WindowsOptimizer is a Windows 11 optimization and maintenance suite built around:

**Discover -> Review -> Backup -> Apply -> Verify -> Recover**

It is designed as a long-lived local Windows utility rather than a collection of one-off registry scripts.

## Current capabilities

- PySide6 desktop GUI with category-based operation views
- Windows build, CPU, GPU, RAM, disk and laptop/desktop discovery
- Administrator detection
- Registry snapshots before changes
- Windows System Restore point integration
- Background execution for long-running operations
- Operation verification and machine-readable logs
- Risk/reversibility/restart metadata
- Taskbar, transparency and wallpaper controls
- Windows Game Mode and optional Game DVR control
- Privacy and DNS maintenance controls
- WinGet software inventory, curated Windows 11 app installer, screenshot-app preset and upgrades
- JSON profiles: Minimal / Standard / Gaming / Performance
- Startup inventory
- Power-plan inventory and controlled High Performance activation
- Network adapter/configuration inventory and latency testing
- Repair actions: Explorer, SFC and DISM
- Daily maintenance scheduler with age-based temp/crash cleanup and system health checks
- Managed Microsoft Edge extension installer with bundled Netflix 4K extension

## Product principles

1. Do not blindly apply every tweak.
2. Do not disable Defender, security software, Windows Update, core services or networking in default profiles.
3. Prefer supported Windows settings over undocumented registry hacks.
4. Every behavior-changing operation must explain its trade-off.
5. Performance claims should be measured rather than assumed.
6. Debloat must be selective and reversible, not a destructive package purge.
7. Long-running work must not freeze the GUI.
8. The GUI is only a shell; Windows operations live in testable modules.

## Product direction

The project takes broad feature inspiration from established Windows utilities such as Chris Titus Tech's WinUtil and the archived Windows Powertool, while implementing an independent Python architecture. Mature utilities demonstrate the value of combining installs, tweaks, fixes, updates, presets and reversible operations in one workflow.

## Roadmap

### Engine
- [x] Discovery
- [x] Operation catalog
- [x] Backup
- [x] Restore point integration
- [x] Background executor
- [x] Operation logging
- [x] Verification foundation
- [ ] Full rollback transactions

### Windows management
- [x] Startup inventory
- [x] Power-plan inventory
- [x] Network adapter/configuration inventory
- [x] Latency test
- [ ] Startup impact analysis and safe disable controls
- [ ] Services analyzer with conservative recommendations
- [ ] Network repair workflow
- [ ] Windows Update center

### Software
- [x] WinGet inventory
- [x] Curated installation
- [x] Upgrade All
- [ ] Uninstall UI
- [ ] Selective debloat
- [ ] Reinstall/restore paths

### Gaming
- [x] Game Mode
- [x] Game DVR control
- [ ] Hardware-aware gaming profile
- [ ] Background-process analysis
- [ ] Before/after benchmark mode

### Software installer
- WinUtil-style searchable, categorized WinGet application catalog
- Multi-select installation with exact package IDs and source selection
- FOSS filter and screenshot-app quick preset (Chrome, Steam, Netflix, qBittorrent, Spotify, PowerShell and OneNote)
- Microsoft Store packages are explicitly marked instead of being mixed silently with winget packages

### Browser integrations
- [x] Bundled Edge extension preparation/installation workflow
- [x] Edge extension management page launcher
- [ ] Extension signature/update verification

### Maintenance
- [x] Daily Task Scheduler integration
- [x] Missed-run recovery via StartWhenAvailable
- [x] Age-based temporary-file cleanup
- [x] Crash/minidump retention cleanup
- [x] Daily memory-pressure, storage, startup/service and pending-reboot checks
- [ ] Optional user-configurable maintenance policies

### Profiles & automation
- [x] JSON profile foundation
- [ ] Import/export
- [ ] Dry-run preview
- [ ] Apply report
- [ ] Scheduled maintenance
- [ ] Signed releases

## Run

    py -m pip install -r requirements.txt
    py main.py

## Build

Run build.bat to produce the Windows executable.

The goal is a clean, explainable optimizer that grows into a serious Windows management tool without becoming an unsafe "apply everything" script.
