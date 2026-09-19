# Approved profile execution

The profile workflow is intentionally review-first:

1. Load a named profile.
2. Build an additive operation plan from current state.
3. Review every actionable operation.
4. Explicitly approve the individual operations to run.
5. Create one registry backup for the approved batch.
6. Execute approved items in order.
7. Verify each item where a supported check exists.
8. Persist one execution receipt containing per-item status and the backup path.

Unknown catalog applications are shown as **SKIP** and are never executable through the approval dialog.

The workflow does not treat a Windows System Restore point as an operation-level rollback. Windows System Restore is a separate recovery mechanism; it restores monitored system state to a restore point and is not a substitute for precise per-operation rollback.

## Safety boundaries

- Profile execution is additive.
- Items removed from a profile are not automatically disabled or uninstalled.
- No wildcard AppX or Windows Feature operations are introduced by profile execution.
- Administrator access is required before execution.
- Long-running Windows operations run through the existing background job runner.
- Receipts are append-only JSON records under the application's backup area.

## Recovery

The registry backup is created before the approved batch starts. This is a recovery aid, not a promise that every operation can be reversed automatically. Operation-specific rollback should be added only where the underlying Windows change has a reliable inverse.
