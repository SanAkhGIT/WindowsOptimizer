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
