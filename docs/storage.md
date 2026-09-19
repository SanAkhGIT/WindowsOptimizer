# Storage Center

Storage Center follows a review-before-delete model.

## Sources and cleanup

Windows Storage Sense can manage temporary files, Recycle Bin cleanup, Downloads thresholds and execution cadence. The application therefore exposes Windows Storage Sense and Cleanup recommendations directly instead of attempting to replace those supported workflows.

The center also supports:
- user temporary files older than 48 hours
- user crash dumps older than 14 days
- Windows Update download cache review/cleanup
- Recycle Bin status and explicit emptying
- Windows Disk Cleanup launch
- system-drive free-space analysis

Microsoft documents the Windows Disk Cleanup command-line utility as cleanmgr.exe and documents cleanup categories including temporary files and Recycle Bin files.

Delivery Optimization normally manages its own cache automatically; Microsoft also documents Disk Cleanup as a supported way to clear Delivery Optimization files when disk space is needed.

## Safety boundaries

The application does not automatically delete:
- Downloads
- Desktop/Documents/Pictures
- browser profiles
- application caches wholesale
- arbitrary files based only on filename
- Windows component-store files

Cleanup actions are explicit and report reclaimed space. In-use or inaccessible files are skipped rather than forcing deletion.

## Future

The next storage work should add:
- Recycle Bin per-drive accounting
- cleanup history
- before/after free-space verification
- Windows Update/Delivery Optimization size reporting
- large-file browser with exclusions
- Storage Sense configuration inspection
