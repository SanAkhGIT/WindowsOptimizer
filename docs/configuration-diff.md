# Configuration Diff & Apply

A loaded WindowsOptimizer configuration is treated as a desired selection, not as permission to make every possible inverse change.

## Review

The Optimize page can calculate a diff showing:

- tweaks that should be selected
- tweaks currently selected but absent from the profile
- application IDs selected by the profile
- Windows Optional Features that should be enabled
- unknown application IDs

The feature inventory uses the Windows Optional Feature state reported by Get-WindowsOptionalFeature. Microsoft documents that cmdlet as the supported way to inspect optional feature state on the running OS. citeturn0search4turn0search5

## Apply policy

Apply Configuration performs only additive operations:

1. create a registry backup
2. apply desired tweaks that are not already selected
3. process the profile's known application catalog
4. enable requested Windows Optional Features that are not already enabled
5. report results

It deliberately does not:

- uninstall applications
- disable Windows Optional Features
- automatically roll back tweaks absent from the profile
- change services
- change networking
- change the active power plan

This is important because an old profile may have been created on a different machine or Windows build.

Microsoft's optional-feature APIs support explicit enable/disable operations and can report whether a restart is needed. WindowsOptimizer keeps those operations explicit rather than treating a profile as an unrestricted Windows image editor. citeturn0search1turn0search6

## Future

A later version can add per-item checkboxes to the diff screen and explicit subtractive actions. Those should remain separately confirmed because removal is materially different from configuration drift correction.
