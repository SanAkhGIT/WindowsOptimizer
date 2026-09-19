# Product roadmap

The project is deliberately borrowing the **product breadth** of mature Windows utilities rather than reproducing their implementation.

## Major product areas

### Install
Curated WinGet catalog, installed inventory, upgrade-all, later search/filter and uninstall. The existing WinUtil project uses an Install surface for browsing, installing, upgrading and uninstalling applications. We are following that proven workflow while keeping our package catalog explicit and auditable.

### Tweaks
Recommended baseline, minimal and advanced tiers, detection of already-applied settings, and explicit undo. WinUtil documents Standard/Minimal/Advanced selection and best-effort installed-tweak detection; our operation model is designed to support the same workflow with stronger per-operation verification.

### Fixes
Network reset, Windows Update repair, system-file repair, WinGet repair and Explorer recovery belong together as maintenance actions rather than being mislabeled as performance tweaks.

### Updates
Inventory available upgrades, allow controlled upgrade-all, and eventually add Windows Update policy controls with clear warnings and rollback guidance.

### Debloat
Use an explicit package catalog and detect installed state first. Removal should be opt-in, package-specific and paired with a reinstall path where Windows supports one. Never make a giant wildcard removal script the default.

### Automation
Profiles should become portable configuration files. A future dry-run mode should show the exact operations a profile would perform before anything changes.

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
