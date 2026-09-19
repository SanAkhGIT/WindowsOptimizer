# Windows Optimizer

WindowsOptimizer is a Windows 11 optimization and maintenance suite built around:

**Discover -> Review -> Backup -> Apply -> Verify -> Recover**

It is designed as a long-lived local Windows utility rather than a collection of one-off registry scripts.

## Current capabilities

- Modern PySide6 desktop GUI with sidebar navigation, live system cockpit and centralized dark theme
- Windows build, CPU, GPU, RAM, disk and laptop/desktop discovery
- Administrator detection
- Registry snapshots before changes
- Windows System Restore point integration
- Background execution for long-running operations and hardware telemetry
- Operation verification and machine-readable logs
- Risk/reversibility/restart metadata with live Applied / Not Applied / Conflict state detection
- Taskbar, transparency, wallpaper and taskbar End Task controls
- Windows Game Mode and optional Game DVR control
- Privacy controls for advertising ID, tailored experiences and Windows activity history
- Essential Windows policy controls with safe conflict detection and owned rollback
- WinGet software inventory, curated Windows 11 app installer, screenshot-app preset and upgrades
- JSON profiles: Minimal / Standard / Gaming / Performance
- AppX package inventory and selective debloat with protected-package safeguards
- Startup inventory
- Power-plan inventory and controlled High Performance activation
- Network adapter/configuration inventory and latency testing
- Windows Optional Features inventory with exact-name enable/disable controls
- Windows Update service/reboot status and conservative component-cache reset
- Repair Center: Explorer, SFC, DISM CheckHealth/ScanHealth/RestoreHealth and Windows Update reset
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
- [x] Owned-policy rollback for new essential tweaks
- [x] Centralized UI theme and responsive dashboard

### Windows management
- [x] Startup inventory
- [x] Power-plan inventory
- [x] Network adapter/configuration inventory
- [x] Latency test
- [x] Startup impact analysis foundation
- [x] Services analyzer with conservative recommendations
- [ ] Safe service/startup editors with per-item rollback
- [ ] Network repair workflow
- [x] Windows Optional Features inventory and guarded enable/disable
- [x] Windows Update status and component reset
- [ ] Full Windows Update policy/update-history center

### Software
- [x] WinGet inventory
- [x] Curated installation
- [x] Upgrade All
- [ ] Uninstall UI
- [x] AppX inventory and selective debloat
- [x] AppX protected-package classification
- [x] Existing-package registration recovery path
- [ ] WinGet/AppX restore catalog

### Gaming
- [x] Game Mode
- [x] Game DVR control
- [ ] Hardware-aware gaming profile
- [ ] Background-process analysis
- [ ] Before/after benchmark mode

### Software installer
- WinUtil-style searchable, categorized WinGet application catalog
- Multi-select installation with exact package IDs and source selection
- FOSS filter and screenshot-app quick preset (Chrome, Steam, Netflix, qBittorrent, Spotify, PowerShell, LM Studio, Stremio, JDownloader 2 and Bluetooth Audio Receiver)
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
- [x] Standard profile expanded with conservative privacy/UI baseline
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


## UI architecture

The desktop shell is intentionally thin: navigation and presentation live in `app.py` and `ui/`, while Windows operations remain in `core/` and `modules/`. The Overview page separates fast telemetry from slower inventory collection so PowerShell/CIM queries do not block the interface.

The dashboard refresh model is deliberately tiered:
- CPU/GPU/RAM/system-drive telemetry: every 2 seconds, one PowerShell round-trip
- Temperature/fan sensors: every 10 seconds, one batched query when firmware exposes them
- BIOS, motherboard, network and driver inventory: on demand/background refresh

The interface avoids an "apply everything" home screen. High-impact operations remain explicit and retain backup, confirmation, verification and administrator guards.
