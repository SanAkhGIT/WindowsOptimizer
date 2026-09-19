# Tweak documentation

Each tweak should be backed by current Microsoft documentation or a Windows API-supported behavior.

## Taskbar alignment

Registry:
`HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced`

Value:
`TaskbarAl`

0 = left
1 = center

The implementation should verify the value after writing it.

## Transparency

Registry:
`HKCU\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize`

Value:
`EnableTransparency`

0 disables transparency effects for the current user.

## Future modules

Before implementing additional tweaks, document:

- Windows build support
- evidence/source
- current behavior
- expected effect
- rollback
- restart/sign-out requirement
- known side effects
