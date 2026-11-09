# Native Windows display review

Findings: [REVIEW.md](REVIEW.md). Recorded JSON and selected screenshots are in
`results/`. A nonzero review exit code is expected while documented failures remain.

## Existing VM setup

Virtual Display Driver 25.7.23 is installed as `ROOT\DISPLAY\0000`, with settings
in `C:\VirtualDisplayDriver\vdd_settings.xml`. It provides two secondary screens.
Supported test resolutions include 800×600, 1024×768, 1280×800, 1366×768,
1920×1080, 2560×1440, 3840×2160, 1080×1920 and 3440×1440 at 60 Hz.
The original VM display remains primary. The original driver XML was saved outside
the repository before changing it.

On a new Windows machine, use the upstream
[Virtual Display Driver instructions](https://github.com/VirtualDrivers/Virtual-Display-Driver)
to install the driver and configure two monitors and the modes above. The winget
package installs the controller; installing the actual display driver is a
separate step. This VM required trusting the verified catalog's SignPath publisher
in the machine's `TrustedPublisher` store. Driver signing enforcement was not
disabled, and test-signing mode was not enabled.

## Run from PowerShell

Run `uv sync --locked` in the project first. A user must be signed into the Windows
desktop. The wrapper schedules Python in that interactive session, so it can also
be invoked by a session-0 administrator. No account password is stored in the task.

```powershell
pwsh -File dev/windows-review/Run-Review.ps1 -Mode Inventory
pwsh -File dev/windows-review/Run-Review.ps1 -Mode Matrix
# Run Hotplug from an elevated PowerShell:
pwsh -File dev/windows-review/Run-Review.ps1 -Mode Hotplug
```

Windows PowerShell 5.1 also works. If local script execution is disabled, invoke
`powershell.exe -NoProfile -ExecutionPolicy RemoteSigned -File ...` for this script.
The wrapper removes its temporary scheduled task when finished and restores the
VDD device if a hotplug test fails while it is disabled. Use a fresh output
directory for every hotplug cycle. Default output is timestamped under ignored
`local-results/`; set `-OutputDirectory` to choose another location.

To run directly from an interactive desktop terminal:

```powershell
uv run --locked python dev/windows_review.py --output inventory.json
uv run --locked python dev/windows_review.py --matrix --output matrix-results
```

The matrix refuses to change a primary or non-VDD output. It restores the target's
initial display mode in `finally`. Hotplug mode needs the wrapper to disable and
re-enable the actual driver while the GUI processes native screen events.

## Coverage limits

The native Windows adapter, Qt screen objects, output windows and local HEROS
transport are real. File chooser return paths are supplied by the test. This does
not substitute for optical output, physical monitor metadata, native mixed-DPI or
taskbar-hover validation. See the review for exact scope and outstanding findings.
