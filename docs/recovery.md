# Recovery model

WindowsOptimizer uses three distinct recovery layers:

1. **Operation rollback** — a precise inverse implemented by the same subsystem. Registry-backed tweaks can now persist rollback metadata and restore only the captured values for that operation.
2. **Registry backup restore** — restores the specific registry values captured by the pre-operation backup manifest. This is broader and can overwrite later changes, so the GUI requires explicit confirmation.
3. **Windows System Restore** — a separate Windows recovery mechanism. It is not treated as an operation-level undo.

Microsoft documents reg save/reg export as supported Windows registry backup mechanisms, while Checkpoint-Computer creates a System Restore point on supported Windows client systems. System Restore has its own Windows-level retention and recovery behavior and should not be conflated with WindowsOptimizer's precise operation receipts.

## Current rollback capabilities

- Tweak: available when the tweak declares either a safe rollback callable or persistent registry rollback metadata plus post-change verification.
- Windows Optional Feature enable: available as the inverse disable operation when the feature was enabled through an additive profile plan.
- WinGet application install: no automatic uninstall rollback is claimed yet.

A failed rollback produces ROLLBACK_FAILED and leaves the original receipt available for investigation.

Registry backup manifests preserve the original value type and binary values where applicable. Targeted restore validates that the current tweak still reports its expected post-change state before replaying the captured values, reducing the risk of overwriting a later manual change. Backup directory names include microseconds to avoid same-second collisions.
