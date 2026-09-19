# Developer & Remote Access Center

The Developer Center is intentionally read-first. It inventories WSL, OpenSSH, PowerShell 7, .NET, Git, Windows optional features and Developer Mode, while exposing supported Windows entry points.

## WSL

Microsoft documents `wsl --install` as the supported one-command setup for WSL, enabling required components and installing a default Linux distribution; a restart can be required. The application uses `--no-launch` so installation does not unexpectedly open a distribution.

WSL supports Windows 11 and recent Windows 10 builds, and Microsoft documents `wsl --status` and `wsl --list --verbose` for diagnostics.

## Developer Mode

Microsoft documents Developer Mode under the Windows developer settings. On current Windows 11 releases, the location is under System > Advanced > For developers. Enabling it requires administrator access. Developer Mode can enable additional deployment/debugging features and can configure SSH-related development functionality.

The application does not silently enable Developer Mode.

## OpenSSH

OpenSSH Server is managed through the Windows `sshd` service. The center only starts or stops it after explicit confirmation and administrator checks. It does not rewrite sshd configuration or open arbitrary firewall ports.

## Environment

The center provides direct access to environment variables and Windows Terminal and reports installed Git, PowerShell 7 and .NET where detectable.

## Safety

- no automatic Developer Mode activation
- no automatic SSH exposure
- no firewall rule creation
- no SSH configuration rewriting
- WSL installation requires explicit confirmation
- privileged operations require Administrator access


## Diagnostic logging

WindowsOptimizer initializes process-wide diagnostic logging when the application starts.

Log location:
`%LOCALAPPDATA%\\WindowsOptimizer\\Logs`

Files:
- `session_<id>.log` — the current application run, including startup, GUI operations, background jobs, subprocess results, registry mutations, backup activity, errors, and uncaught exceptions.
- `application.log` — rolling longer-term history.
- `session_<id>_crash.log` — low-level Python fatal-error diagnostics when the platform can capture them.

Session logs are capped with rotation so a broken or unusually noisy operation cannot grow logs without bound. Python's `RotatingFileHandler` is used for bounded log files. The log subsystem is initialized before the GUI starts. Startup records the session and crash-log paths before Qt window construction, and GUI startup is wrapped as a fatal startup boundary so import, Qt initialization, theme setup, and main-window construction failures are logged with tracebacks.

Do not put passwords, API keys, or other secrets into operation arguments or diagnostic messages; diagnostic logging records operation arguments to make failures reproducible.
