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
- Power Center with built-in plans and battery report
- Guarded Service Center for startup mode changes
- DNS Center with DHCP/Cloudflare/Google/Quad9 presets and cache flush
- Storage analyzer for system-drive and safe cleanup-category sizing
- Gaming Center with GPU, Game Mode, Game DVR, HAGS and Xbox-service diagnostics
- Repair Center: Explorer, SFC, DISM CheckHealth/ScanHealth/RestoreHealth and Windows Update reset
- Daily maintenance scheduler with age-based temp/crash cleanup and system health checks
- Managed Microsoft Edge extension installer with bundled Netflix 4K extension
- Android TV Control Center over ADB: device/launcher health, disabled-package inventory, memory/DNS/background diagnostics, review-first optional debloat, and exact local undo for recorded reversible changes
- Android TV UI controls: left-side navigation, per-package toggles plus confirmed bulk enable/disable for detected reviewed optional apps, switch between official TV Detox, FIZXIX Home and Google TV Home, edit launcher tiles/shortcuts with backup safeguards, animation presets, reversible screensaver and plugged-in display-sleep controls
- Optional cache trim and ART speed-profile compilation, explicitly marked as operations without an exact inverse; no app uninstall path

## Product principles

1. Do not blindly apply every tweak.
2. Do not disable Defender, security software, Windows Update, core services or networking in default profiles.
3. Prefer supported Windows settings over undocumented registry hacks.
4. Every behavior-changing operation must explain its trade-off.
5. Performance claims should be measured rather than assumed.
6. Debloat must be selective and reversible, not a destructive package purge.
7. Long-running work must not freeze the GUI.
8. The GUI is only a shell; Windows operations live in testable modules.
9. Android TV management uses a separate ADB module and never feeds device packages into the Windows AppX debloater.
10. Android TV package changes use a strict optional-package allowlist, require an explicit per-package confirmation in the UI, verify their result, and never uninstall apps.
11. Launcher changes must verify the resolved Home activity and attempt to restore the prior Home on failure; stock launcher/setup packages are not blindly disabled.

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

## TV Detox upstream sync and FIZXIX Home publishing

- The FIZXIX build fetches the current TV Detox upstream default-branch revision by default. For reproducible builds, set \`TV_DETOX_REF\` to a tag or commit SHA.
- The **Build FIZXIX TV Detox** workflow can be run manually with an upstream branch/tag/commit and also runs weekly. The build records the exact upstream commit in \`FIZXIX-TV-Detox-UPSTREAM-COMMIT.txt\` and its notice file.
- The normal Windows executable workflow builds the branded APK, embeds it into WindowsOptimizer, runs Python tests and compilation, then publishes the EXE and APK provenance as one artifact.
- Upstream source changes that no longer match the expected patch anchors intentionally fail the build rather than silently producing an incorrectly modified launcher. Review and adapt the patch when upstream UI internals change.
- Installation on a Google TV device is an ADB sideload action initiated by the user in WindowsOptimizer; CI does not connect to or silently change a TV. This is not Google Play Store publication. Play Store distribution requires the relevant developer account, signing, listing, policy and review steps.
- For in-place updates of an already installed FIZXIX Home, configure the persistent signing secrets \`FIZXIX_TVHOME_KEYSTORE_BASE64\` and \`FIZXIX_TVHOME_KEYSTORE_PASSWORD\`. Without the same signing key, Android may reject updates; the tool must not auto-uninstall the existing launcher.

## Android TV Control Center

1. Connect the Windows PC and Android/Google TV to the same network. Enable network ADB on the TV and authorize the PC on the TV's prompt.
2. Open **Android TV** from the sidebar. Enter the TV's IP and ADB TCP port (classic ADB is commonly port 5555) and select Google Platform-Tools adb.exe if automatic discovery does not find it.
3. Run **Read device health** first. It is read-only and reports the active Home component, enabled/disabled launchers and setup package, disabled package inventory, MemFree and MemAvailable separately, private DNS, animation/screensaver settings, and background state for known media apps.
4. Debloat candidates are optional and device-dependent. The table does not preselect packages; use one package at a time and read its trade-off. Google Play/GMS/GSF, Settings, System UI, permission controller, WebView, TTS, keyboard/input, Bluetooth/CEC/input, remote-pairing, OTA/upgrade, setup, and Droidlogic/SDT vendor packages are excluded from the debloat allowlist.
5. Home switching captures the previous Home, verifies the new component, and attempts rollback if verification fails. Restoring Google TV Home may re-enable com.google.android.apps.tv.launcherx; it does not uninstall tv-detox or change the setup wizard. **Emergency recovery command for the configured TV:**

   adb -s 192.168.0.21:5555 shell pm enable com.google.android.apps.tv.launcherx

6. The Launcher & UI tab can edit the tile order and Bluetooth/Sound/Picture shortcuts for either **Official TV Detox** or **FIZXIX Home**. It reads preferences through Android's run-as interface where available; if the APK blocks readback, use the manual-snapshot mode and enter the current app tile package IDs in exact on-screen order (or explicitly confirm automatic discovery) and current shortcuts. The snapshot becomes Undo's restore state; do not guess these values.
7. To build the black **FIZXIX Home** launcher, open the [FIZXIX APK build workflow](https://github.com/SanAkhGIT/WindowsOptimizer/actions/workflows/build-fizxix-tv-detox.yml), open its latest successful run, and download the **FIZXIX-TV-Detox** artifact. Extract **FIZXIX-TV-Detox.apk**, select it in Windows Optimizer, then choose **Set FIZXIX Home as Home** if desired. It installs side-by-side as `com.fizxix.tvhome`; official TV Detox is not replaced. Build artifacts expire after 30 days. Unless repository secrets `FIZXIX_TVHOME_KEYSTORE_BASE64` and `FIZXIX_TVHOME_KEYSTORE_PASSWORD` are configured with a persistent signing key, a later build may not update an already-installed FIZXIX APK in place. The tool never uninstalls it automatically.
8. Reversible changes are recorded in %LOCALAPPDATA%\WindowsOptimizer\android-tv\changes.jsonl. **Undo latest reversible change** replays one exact inverse at a time, newest first. Cache trimming and ART recompilation are recorded as having no automatic inverse; they remain untouched and are named in the undo result while the tool finds the newest reversible change.

Android TV functionality is inspired by and designed to interoperate with [Ansub/tv-detox](https://github.com/Ansub/tv-detox), an MIT-licensed home screen. The official installer reads release metadata, verifies the published SHA-256 digest, and never uninstalls an incompatible package. The optional FIZXIX build downloads a pinned upstream source revision during CI and applies only the black background, bottom-right watermark and separate package ID; it does not replace the official application source or modify a connected TV during build.

The goal is a clean, explainable optimizer that grows into a serious Windows management tool without becoming an unsafe "apply everything" script.


## UI architecture

The desktop shell is intentionally thin: navigation and presentation live in `app.py` and `ui/`, while Windows operations remain in `core/` and `modules/`. The Overview page separates fast telemetry from slower inventory collection so PowerShell/CIM queries do not block the interface.

The dashboard refresh model is deliberately tiered:
- CPU/GPU/RAM/system-drive telemetry: every 2 seconds, one PowerShell round-trip
- Temperature/fan sensors: every 10 seconds, one batched query when firmware exposes them
- BIOS, motherboard, network and driver inventory: on demand/background refresh

The interface avoids an "apply everything" home screen. High-impact operations remain explicit and retain backup, confirmation, verification and administrator guards.
