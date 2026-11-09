
# Changelog

## Unreleased

Changes prepared on `master-testing` for the next merge into `master`. The release version and date will be assigned with the version bump.

### Added

- Monitor bits-per-channel detection from EDID, displayed in physical monitor details when available.
- HEROS modification setters for X, Y, Z, wavelength, focal length, magnification and pixel pitch.
- Adjustable UI scaling through sidebar controls and keyboard shortcuts.
- Regression tests for remote parameter synchronization, client/server contracts, monitor identity, geometry changes and session behavior.

### Changed

- Replaced tabbed pattern editing with simultaneously visible controls, including a two-column Zernike layout.
- Matched all five preview surfaces to the selected screen's aspect ratio and scaled translucent `Off` overlays with preview dimensions.
- Moved shared phase conversion and file helpers into the standalone client, retaining server compatibility imports.
- Limited default notebook preview sampling to about one million pixels; `max_preview_pixels=None` requests native sampling without changing SLM output data.
- Coalesced asynchronous pattern edits and discarded stale calculation results.
- Separated output status from its enable/disable action and updated slider values immediately during dragging.
- Hid the unstable HEROS connection toggle from the UI while preserving its functionality and saved configuration preference.

### Fixed

- Remote Zernike and modification values now update the corresponding desktop controls. Remote shifts expand the slider range without exposing a HEROS setter for slider max shift.
- Geometry/DPI changes trigger monitor rescans and reset patterns and optical parameters when output dimensions change.
- Stabilized monitor identity ordering, added a connector-based fallback for screens without EDID, and handled duplicate IDs without overwriting sessions.
- Preserved disconnect handling when monitor metadata is no longer available.
- Added output-window focus prevention and Windows Aero Peek exclusions; native platform validation remains necessary.
- Aligned the unitless magnification field with the other modification inputs.
- Made pattern flip mapping explicit, preserved float32 byte transport, and deferred client network discovery until requested.
- Improved application shutdown handling for termination signals while the Qt event loop is idle.

### Remaining limitations

- Output remains 8-bit even when a monitor reports greater precision.
- The Enable SLM output button overlap still needs a design revision, and the HEROS connection toggle remains hidden pending stabilization. See [development notes](DEV_NOTES.md).
- Offscreen checks do not validate physical SLM output, native Windows behavior, or Linux compositor/mirrored-monitor combinations. See the platform validation notes in the development notes.

---

### 26-09-16

Version Bump: 0.3.4.post3

##### Added:
- Export / Import Config
- Button to reset current SLM session

##### Changed:
- Made Zernike Pattern, Modification Pattern initialization async

### 26-09-15

Version Bump: 0.3.3.post3

##### Added
- If you click a window multiple times, a small cross appears in the top right corner, to close the window
  - This was added in case one accidentally opens a window on the primary screen

##### Changed
- Window name is now "{Display Name} - {Screen UID}"

### 26-09-14

Version Bump: 0.3.3

##### Added:
- Changing Zernike Coefficients is now accessible via Heros
- CHANGELOG.md
- Added host_id into UID generation
- Added monitor serial numbers into UID generation

##### Changed:
- Added Date to console timestamp
- Console is now resizable
- more exhaustive logging on exiting the app

---

### 26-09-09

Version Bump: 0.3.1 -> 0.3.2

##### Breaking Changes:

- getPatternInclusion now returns dict instead of tuple of bools

##### Added:

- Toggling of SLM windows is now exposed into api
- log that session initialized
- log that heros activated

##### Changed:

- Moved Total Hologram to top left
- Crossing out inactive holograms instead of making them gray
- Total sum is also crossed out when SLM window is deactivated
- when screen is disabled, cross out the preview of the sums of the holograms
- Changing a Pattern will set it to active

##### Fixed:

- add timestamps to the logs
- Error message is green (Windows) "Error importing base aberration: cannot identify image file 'C:\\Users\\morit\\Downloads\\SteelSeriesGG112.0.0Setup.exe.bmp'"
- Refresh Button now actually refreshes the screen list
- using scroll wheel to change slider value now actually works

##### Rejected:

- Default Hologram that displays 0, 255 with a text printed on top, and in the center is a phase vortex to generate donut
