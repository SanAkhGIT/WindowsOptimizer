# Runtime & UI Audit Log — 2026-09-20

## Purpose

Repository-wide follow-up audit after the recent fixes for:

- malformed Python/PowerShell strings and stale imports
- raw CIM/network data displayed in the UI
- SFC/DISM garbled Windows console output
- background-operation lifecycle and stale Qt signal errors
- operations that block the GUI or expose diagnostic output directly to users

This audit checks for the same classes of defects in other modules and records changes made on the `audit/runtime-hardening` branch.

## Findings addressed

### 1. Shared Windows process decoding

**Risk:** Different modules were invoking PowerShell/subprocesses directly and using forced UTF-8 decoding.

**Action:** Routed additional Windows command execution through `core.process.run_executable()`, which now owns Windows-compatible output decoding.

Affected areas:

- scheduler
- maintenance
- system inventory
- restore-point creation
- diagnostics
- network center
- repair center

Also added UTF-16 output coverage for redirected Windows utilities.

### 2. Raw network/CIM objects

**Risk:** Network inventory could return nested CIM metadata instead of user-facing network information.

**Action:** Network configuration now explicitly projects:

- interface alias
- interface description
- IPv4 addresses
- IPv6 addresses
- DNS servers
- network profile
- network category

The UI should consume these fields rather than render CIM objects.

### 3. Background-operation lifecycle

**Risk:** A background QRunnable could finish after its Qt signal owner had already been destroyed, producing:

`RuntimeError: Signal source has been deleted`

**Action:** The global operation lifecycle was hardened so:

- busy operations are explicitly reported to the Activity Center
- completion/error state is recorded before follow-up callbacks
- optimization backup work is moved into the worker
- Windows Update backup + policy change are one background operation
- AppX inventory is lazy-loaded when Debloat is opened instead of occupying the startup operation slot

**Important:** Native Qt shutdown behavior still needs Windows runtime validation.

### 4. Startup inventory classification

**Risk:** Startup registry strings contained invalid Python escapes and scope detection could incorrectly classify HKLM entries as user-manageable.

**Action:**

- corrected Run/RunOnce path handling
- made HKLM/HKEY_LOCAL_MACHINE explicitly System scope
- added a regression test preventing machine startup entries from becoming user controls

### 5. Windows Update policy values

**Risk:** Pause-policy values were being written with an unsuitable value representation.

**Action:** Pause start dates are now written as ISO date strings and covered by tests.

### 6. Developer / Gaming registry paths

**Risk:** Several registry paths had malformed backslashes and could silently query the wrong location.

**Action:**

- corrected Developer Mode registry path
- corrected Game Bar / Game DVR / Graphics Drivers registry paths
- added regression tests for these paths

### 7. Storage / Recycle Bin

**Risk:** Recycle Bin inspection used a fixed C: path.

**Action:** It now derives the current Windows system drive before inspecting the Recycle Bin.

### 8. Maintenance UI

**Risk:** Maintenance status and manual maintenance actions could perform Windows operations on the GUI thread.

**Action:** Schedule checks and maintenance actions are now routed through the background job system.

### 9. Packaged-app writable data

**Risk:** Generated personalization assets were stored relative to the application package, which is unsuitable for a packaged/one-file executable.

**Action:** Generated assets now use:

`%LOCALAPPDATA%\WindowsOptimizer\Assets`

### 10. Duplicate update implementation

**Risk:** The legacy `modules/updates.py` path duplicated WinGet update behavior.

**Action:** It is now a compatibility wrapper around the primary software-update implementation.

### 11. Repository-wide import coverage

Added `tests/test_import_smoke.py` covering the major core/module/UI imports to catch the type of stale API/import errors that previously blocked application startup.

### 12. CI coverage

The Windows build workflow now:

- installs pytest explicitly
- runs Python compilation before tests
- validates pull requests targeting `main`
- continues to build the Windows executable only after the normal validation path

## Existing bugs confirmed from the previous user runtime session

The following failures were reproduced/reported during the development session and are now part of the audit history:

1. malformed `modules/services.py` string literals
2. invalid startup regex/string escapes
3. malformed Developer Mode registry path
4. stale `storage_center.categories` imports in two locations
5. raw CIM network object rendering
6. transient startup/background Qt signal lifetime failure
7. missing pytest in the local/CI environment
8. SFC/DISM Windows console encoding corruption
9. optimizer operations becoming ineffective after multiple selections
10. expensive AppX inventory competing with normal UI operations
11. maintenance actions not consistently isolated from the GUI thread

## Validation status

### Static validation

- `python -m compileall -q .` has been used repeatedly during the development session.
- The audit adds an import-smoke test and additional regression tests.

### Runtime validation still required

The assistant cannot execute the user's Windows desktop environment directly. The following must be validated on the user's machine and/or Windows CI:

- full pytest suite
- SFC / DISM execution
- WinGet update discovery and upgrade
- AppX inventory/removal
- Startup controls
- Services controls
- Windows Update policy operations
- Developer Mode / WSL operations
- DNS operations
- Storage cleanup
- Gaming diagnostics
- maintenance Task Scheduler operations
- System Restore creation
- packaged/one-file EXE startup
- application shutdown while a background operation is active

## Quality rule going forward

WindowsOptimizer should follow this boundary:

**Backend**
- structured result
- explicit success/failure
- exit code
- machine-readable fields

**Activity Center**
- current operation
- Waiting / Working / Verifying / Complete / Error
- elapsed time
- progress when trustworthy
- concise live messages

**Diagnostic log**
- full command output
- stderr
- traceback
- operation metadata
- receipt/backup paths

Raw PowerShell/CIM/console output should not be rendered directly in normal UI cards.

## Audit branch

Branch:

`audit/runtime-hardening`

Base:

`main`

The branch contains the hardening changes and tests described above. It should be merged only after Windows CI/local runtime validation confirms that the affected operations behave correctly.
