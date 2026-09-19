# Execution Receipts

WindowsOptimizer now treats an execution as an auditable operation rather than
only a console message.

Each completed execution can produce a JSON receipt containing:

- unique receipt ID
- UTC creation time
- source and optional profile identity/version
- backup location, when one was created
- overall status
- one item per attempted operation
- operation status and verification message

## Statuses

- `VERIFIED`: the operation completed and its check reported success.
- `COMPLETED_WITH_WARNINGS`: an operation completed but verification was not
  conclusive.
- `FAILED`: at least one operation failed.

Receipts are stored below:

`%USERPROFILE%\\WindowsOptimizerBackups\\receipts`

This is deliberately separate from the configuration file. A profile describes
desired state; a receipt records an actual execution.

## Safety boundary

The receipt system does not itself execute commands or perform rollback.
It records the result of operations already approved by the user.

The next stage is to connect plans to per-item approval and execution, then add
operation-specific rollback metadata where it is genuinely supported.

## Restore points

Windows System Restore is a separate recovery layer. Microsoft documents
`Checkpoint-Computer` for creating restore points on Windows client editions,
and the System Restore API supports explicit restore-point creation. Restore
points are not treated as a substitute for operation-level rollback.
