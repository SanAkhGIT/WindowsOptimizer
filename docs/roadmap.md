# Product roadmap

The project is deliberately borrowing the **product breadth** of mature Windows utilities rather than reproducing their implementation.

## Major product areas

### Install
Curated WinGet catalog, installed inventory, upgrade-all, later search/filter and uninstall. The existing WinUtil project uses an Install surface for browsing, installing, upgrading and uninstalling applications. We are following that proven workflow while keeping our package catalog explicit and auditable.

### Tweaks
Recommended baseline, minimal and advanced tiers, detection of already-applied settings, and explicit undo. The current catalog now includes consumer-experience, activity-history, tailored-experience, taskbar End Task and advanced WPBT controls. Policy-backed tweaks refuse to overwrite conflicting existing policies and track changes made by the current operation for safer rollback.

### Fixes
Network reset, Windows Update repair, system-file repair, WinGet repair and Explorer recovery belong together as maintenance actions rather than being mislabeled as performance tweaks. The current repair center now separates DISM CheckHealth, ScanHealth and RestoreHealth, plus SFC and Windows Update component reset.

### Updates
Inventory available upgrades, allow controlled upgrade-all, and expose Windows Update service/reboot status. The current component reset renames the SoftwareDistribution and catroot2 caches instead of deleting them, retaining a recovery path. Full Windows Update policy, pause/resume and history management remains separate because supported controls vary by Windows build.

### Debloat
Use an explicit package inventory and detect installed state first. The current AppX surface classifies framework/non-removable/protected packages, marks common unwanted packages as recommendation hints, and removes only exact selected package full names. Existing installation folders can be registered again when Windows still has the package files. Future work should add provisioned-package management and stronger restore catalogs.

### Automation
Profiles should become portable configuration files. A future dry-run mode should show the exact operations a profile would perform before anything changes. The Standard profile now reflects the project's conservative privacy/UI baseline rather than only legacy UI toggles.

### Windows Features
Inventory optional Windows features and allow exact-name enable/disable actions. Feature changes use the supported DISM PowerShell cmdlets and never accept wildcard feature names from the UI. Reboot requirements are surfaced from Windows.

### Windows 11 Creator
A future advanced subsystem can build a customized Windows 11 image from an official Microsoft image. This is intentionally separated from live-system optimization because image servicing has different risks and validation requirements.

## Quality gates

Before a subsystem graduates from experimental to normal use:

1. Static validation and unit tests.
2. Supported Windows build documented.
3. Exact operation and expected state documented.
4. Apply and detection paths implemented.
5. Failure behavior is explicit.
6. Rollback strategy identified.
7. GUI work is moved off the UI thread for long operations.
8. No default action disables security, update infrastructure or core networking.
9. Performance claims are measured rather than assumed.
