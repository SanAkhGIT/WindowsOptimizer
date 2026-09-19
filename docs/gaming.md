# Gaming Center

Gaming Center is intentionally diagnostic-first.

## What it reports

- GPU name, driver version/date, video processor and status
- Windows version/build
- Game Mode registry state
- Game DVR capture state
- raw HAGS configuration value when Windows exposes it
- active power plan
- Xbox-related service state

Windows' Game Mode is already part of the operating system gaming model; Microsoft notes that Game Mode is enabled by default for most Windows games. The project therefore does not claim that a generic "optimizer" toggle creates a guaranteed FPS increase. citeturn0search0turn0search11

## Graphics settings

The center provides shortcuts to Windows Graphics settings and Game Mode/Game Bar settings. GPU preference is a Windows graphics-policy decision; Microsoft's DXGI API distinguishes minimum-power and high-performance GPU preferences. citeturn0search14

## HAGS and MPO

HAGS and MPO are reported/treated as diagnostics rather than universal optimization switches. Microsoft documents GPU scheduling as part of the Windows graphics stack and MPO as hardware-assisted composition. citeturn0search10turn0search4

The application does not force HAGS, disable MPO, or alter fullscreen optimization globally because those changes can be workload- and driver-dependent.

## Xbox services

Xbox service state is shown for troubleshooting. The application does not mass-disable Xbox services because some gaming features depend on them.
