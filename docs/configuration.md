# Configuration & Profiles

WindowsOptimizer now supports a portable JSON configuration snapshot.

## What is captured

A configuration contains:
- schema version
- selected WindowsOptimizer tweak IDs
- selected curated WinGet application IDs
- enabled Windows Optional Feature names at export time
- active power-plan diagnostic text
- maintenance metadata reserved for future scheduling/profile support

The format is intentionally product-owned rather than pretending to be a complete Windows image.

## Review-first import

Importing a configuration only changes the current GUI selections.

It does not:
- apply tweaks
- install applications
- enable or disable Windows features
- change the power plan
- change services
- change networking
- change maintenance schedules

The user reviews the imported selections and then explicitly performs the relevant operation.

Unknown tweak and application IDs are ignored and reported. This makes an older configuration safer to open after the catalog changes.

## WinGet export

The Optimize page also exposes native WinGet export. Microsoft documents WinGet export/import as a package-list workflow, while WinGet Configuration provides a broader declarative desired-state mechanism.

For reproducible development environments, Microsoft recommends WinGet Configuration files. Current WinGet Configuration v3 uses the .winget format and DSC v3; WindowsOptimizer does not silently generate or execute arbitrary DSC resources.

Microsoft explicitly warns that configuration files and their DSC resources should be reviewed for trustworthiness before execution.

## Direction

The configuration layer is the foundation for:
1. richer machine snapshots
2. profile versioning
3. diff/preview before changes
4. unattended execution with explicit policy
5. machine-to-machine migration
6. optional WinGet Configuration integration

The key boundary remains: export and import are data operations; applying system changes remains an explicit action.
