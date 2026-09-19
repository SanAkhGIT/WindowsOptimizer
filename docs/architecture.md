# Architecture

WindowsOptimizer is an optimizer engine, not a pile of registry scripts.

## Lifecycle
1. Discover Windows and hardware state.
2. Build an applicable operation catalog.
3. Explain each operation and its trade-offs.
4. Back up state and optionally create a System Restore point.
5. Apply only explicitly selected operations.
6. Verify and log results.

## Risk model
SAFE = low-risk supported user configuration/maintenance.
CAUTION = behavior-changing with a clear trade-off.
ADVANCED = system-level and explicit opt-in.

Security software, Windows Update, core services and networking are never disabled by a default optimization profile.

## Long-term modules
Startup manager, services analyzer, network adapter analysis, power profiles, WinGet software center, reversible debloat, repair center, hardware-aware recommendations, import/export profiles and per-operation rollback.


## Windows management center

The Windows page is a thin UI shell over dedicated management modules.

### Startup
Startup discovery uses the supported Win32_StartupCommand inventory and surfaces registry Run/RunOnce and Startup-folder sources. Microsoft documents Run/RunOnce and Startup folders as core startup mechanisms. citeturn0search0turn0search2

Only current-user Run/RunOnce values are directly editable by the application. Before disabling an entry, its original registry value and type are stored under the user's WindowsOptimizer backup directory. System-wide startup entries remain read-only.

Scheduled tasks are inventory-only for now. This avoids silently changing an autostart mechanism that may have application-specific triggers or conditions.

### Services
Service inventory includes state, startup mode, account, executable path and service metadata. Selected services expose dependency/dependent-service details before changes. Windows service startup order can depend on explicit service dependencies, so the UI does not provide a mass-disable operation. citeturn0search4turn0search11

Startup-mode changes save the original mode before applying the requested mode and can be restored later.

### Verification direction
The next step is post-change verification and a dedicated operation-history view so management changes have the same Discover → Backup → Apply → Verify → Recover lifecycle as tweak operations.
