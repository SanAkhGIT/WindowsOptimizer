# Profile Manager

Windows Optimizer profiles are named, versioned configuration snapshots. They are
data only: loading or saving a profile never changes Windows state.

## Storage

Built-in profiles remain in the repository under `profiles/` and are read-only.
User-created profiles are stored at:

`%LOCALAPPDATA%\\WindowsOptimizer\\Profiles`

Writes use a temporary file followed by an atomic replace so a partially-written
profile is not treated as a valid profile.

## Schema

A profile contains:

- profile schema version
- stable profile ID
- display name and description
- profile version
- created/updated UTC timestamps
- the existing Windows Optimizer configuration payload

The embedded configuration continues to use the existing configuration schema.
This keeps profile metadata separate from the operations it describes.

## Operation planning

The profile planner compares a profile against the current selections and enabled
Windows optional features. It produces an explicit list of actionable operations.

Current planning is additive:

- select/apply missing tweaks
- install missing catalog applications
- enable requested Windows optional features
- report unknown application IDs as skipped

The planner does **not** automatically remove applications, disable Windows
features, or roll back tweaks that are absent from the profile.

This is deliberate. The plan is the review boundary before execution.

## Versioning

Saving an existing custom profile increments its integer version while preserving
its original creation timestamp. Built-in profiles cannot be overwritten or
deleted.

## Future extension

The planner is designed to grow into per-item approval, execution receipts,
rollback metadata, and unattended execution without changing the profile file
format into an opaque script.
