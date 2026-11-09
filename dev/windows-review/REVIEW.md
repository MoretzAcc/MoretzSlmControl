# Windows review — 2026-11-09

Reviewed upstream 0.3.5 (`ebfcd42`) with a local startup fix, then packaged as
`0.3.5+moretzai.1`. Development branch: `fork-windows` in
`MoretzAccAi/MoretzSlmControl`. Fork master was synchronized with upstream while
preserving its previous merge commit; no history was rewritten.

## Environment and method

- Windows 11 x64 VM, CPython 3.14.10, PySide6 6.11.1, locked dependencies.
- Native Windows Qt platform in the interactive desktop session; not offscreen.
- Original desktop: Microsoft Basic Display Adapter, 1280×800.
- Two additional outputs supplied by Virtual Display Driver 25.7.23. These are
  native Windows/Qt screens; the production monitor adapter was not mocked.
- The matrix changes only a secondary VDD output and restores its initial mode.
- File dialogs are replaced with known paths to exercise the real import/export
  handlers without manual file selection. Other application behavior is real.
- Zernike calculations, configuration imports, slider edits, and a separate
  HEROS client are exercised at resolutions up to approximately full HD.
  Larger cases still test file import/export, flipping and native output.

## Results

The size matrix contains **116 checks: 113 passed, 3 failed**. All three failures
concern the control window fitting its target work area. The runner deliberately
returns a failing exit status for these outstanding findings.

| Target | Checks | Failed | Control window fits |
| --- | ---: | ---: | --- |
| 800×600 | 18 | 1 | No |
| 1366×768 | 18 | 1 | No |
| 1920×1080 | 23 | 0 | Yes |
| 2560×1440 | 13 | 0 | Yes |
| 3840×2160 | 13 | 0 | Yes |
| 1080×1920 | 18 | 1 | No |
| 3440×1440 | 13 | 0 | Yes |

Verified in the matrix:

- One distinct record per native Qt screen, including identical-model VDD panels.
- Native buffer/pixmap dimensions and exact fullscreen placement on the target.
- NPY hologram import, BMP correction import and horizontal flipping.
- Enable/disable of SLM output without stealing focus from the control window.
- Successful native DWM calls for both Peek exclusion attributes.
- Configuration export dimensions; import and flip-state roundtrip at <= full HD.
- Asynchronous Zernike and modification calculations and live slider feedback.
- Three simultaneous independent outputs with distinct HERO identities.
- Live 1920×1080 → 1024×768 → 1920×1080 changes retain identity and resize buffers.
- A separate client process connects to the actual local HEROS server, sets X=25,
  and synchronizes the control field.

Byte comparisons allow at most one circular gray level because float32 phase
wrapping can move a quantization tie. The QHD ramp differs by one level in 8,640
pixels; other final ramp comparisons are exact. The runner waits for asynchronous
flips instead of assuming a fixed 100 ms delay. Recorded flip completion times
range from about 0.06 s at 800×600 to 0.42 s at 4K; these VM measurements include
test-side copying/comparison and are not an isolated rendering benchmark.

Unit validation: **55 tests ran successfully, one skipped** (Unix signal delivery
is intentionally skipped on Windows). Ruff passed.

## Startup blocker fixed

**Fixed:** without a supported WMI monitor descriptor provider, startup raised
`pywintypes.com_error` with `0x8004100c` while enumerating EDIDs. The application
exited before presenting its window. The Windows adapter now catches this COM
failure, logs a warning and uses the existing Qt metadata/connector fallback.
Successful EDID discovery and other platform branches are unchanged. A Windows
regression test checks that the screen remains available with native dimensions
and a non-empty identity after this error.

This was reproduced before installing VDD; the native entrypoint subsequently
displayed a responding control window on the original VM desktop.

## Improvements still needed

### P1: Make the control window adapt to its current screen

`MainWindow` sizes itself once from the primary screen and fixes its dimensions.
Moving it to another monitor does not adapt to that monitor's available area.
The tested window frame was 1280×748: too large for the 800×552 work area at
800×600, too tall for 1366×720 at 1366×768, and too wide for portrait 1080×1872.
Controls can therefore extend beyond the visible work area.

Use the actual window screen and work area, account for native frame/taskbar
dimensions, and support resizing or scrolling without shrinking all text. Retest
startup on small primary displays and movement across monitors. The matrix
currently starts on the original primary desktop and moves the control window;
it does not claim to have changed the Windows primary-monitor assignment.

### P1: Investigate intermittent hotplug recovery

The first real disable/re-enable cycle of the VDD device passed disconnection
checks but failed to restore one of the two virtual screens and its enabled
output, even after waiting. Only the primary and one original virtual identity
remained connected. Existing sessions were retained, but one window stayed hidden.

A second independently recorded diagnostic cycle passed all nine checks,
including automatic reconnection before manual refresh. A third cycle reproduced
the missed output: Qt already exposed all three screens while the manager listed
only two as connected. Calling the same rescan used by the Refresh button restored
both original identities and enabled windows. This indicates an intermittent
rescan/reconnection problem rather than a permanent identity change; the precise
event-ordering cause is not established. Investigate Qt screen-event ordering and
display/EDID readiness; consider a bounded deferred rescan after Windows topology
changes. Preserve failed evidence and run repeated cycles before marking this fixed.

### P2: Distinguish identical monitors in the sidebar

The two virtual panels have distinct records and HERO identities, but both sidebar
labels read `MTT - VDD_by_MTT`. Show a connector, screen name or short identifier
in the label so users can reliably select the intended output.

### P2: Validate readability and remaining native Windows behavior

The control defaults to 60% UI scale on the 1280×800 desktop and screenshots show
very small text. Provide a usable small-screen layout instead of relying solely
on font reduction. Keep the documented output-button/preview overlap on the design
backlog; this review does not change that layout.

The following are **validation gaps, not confirmed failures**: mixed native
Windows DPI/scaling, physical SLM/EDID mapping, refresh timing, optical fidelity,
precision above eight bits, and taskbar-hover/Show Desktop behavior. DWM setter
success is checked, but it does not establish the final compositor behavior.
Linux was not verified during this Windows review. Full configuration import and
Zernike computation above full HD were not included in the size matrix.

## Evidence and references

- [Machine-readable matrix](results/summary.json), per-scenario JSON and selected screenshots.
- [Initial hotplug failure](results/hotplug.json).
- [Subsequent passing hotplug diagnostic](results/hotplug-diagnostic.json).
- [Repeated failure and successful manual refresh](results/hotplug-wrapper.json).
- [Virtual Display Driver installation/configuration](https://github.com/VirtualDrivers/Virtual-Display-Driver).
- [Microsoft DWM attribute documentation](https://learn.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute).

The DWM Peek attributes are documented for `DwmSetWindowAttribute`, not for reading
with `DwmGetWindowAttribute`. Readback returns `E_INVALIDARG` here and is not counted
as an application failure.
