# Changelog

## 0.3.6.post1 — 2026-11-09

##### Changed:
- Doubled the size of the Off label in inactive previews.
- Default Slider max shift is now 100 µm.

##### Fixed:
- Zernike calculation completion preserves the cursor and text selection while editing.
- Pattern composition frame and heading follow the active Qt style used by the other sections.

## 0.3.6 — 2026-11-09

##### Added:
- Persistent UI scaling preferences, also supported in configuration export/import.

##### Changed:
- Resizable window with scrollable controls and an adjustable sidebar.

##### Fixed:
- Improved Windows monitor handling when EDID queries fail.
- Kept controls and screen information readable when scaling the UI.

## 0.3.5 — 2026-11-09

##### Added:
- Monitor bit-depth information.
- HEROS setters for modification shifts and optical parameters.
- Adjustable UI scaling.

##### Changed:
- All pattern controls are visible together; previews follow the screen aspect ratio.
- Pattern edits calculate in the background and keep the latest result.
- Hid the unstable HEROS connection toggle.

##### Fixed:
- Remote parameter changes update the UI and expand shift slider ranges when needed.
- Improved monitor identification and handling of resolution changes and disconnects.

### 26-09-16

Version Bump: 0.3.4.post3

##### Added:
- Export / Import Config
- Button to reset current SLM session

##### Changed:
- Made Zernike Pattern, Modification Pattern initialization async

### 26-09-15

Version Bump: 0.3.3.post3

##### Added:
- Close button for SLM output windows after repeated clicks.

##### Changed:
- Window name includes the display name and screen UID.

### 26-09-14

Version Bump: 0.3.3

##### Added:
- Changing Zernike coefficients via HEROS.
- Host ID and monitor serial numbers in screen UIDs.

### 26-09-09

Version Bump: 0.3.1 -> 0.3.2

##### Breaking Changes:
- getPatternInclusion now returns a dict instead of a tuple of bools.

##### Added:
- Toggling SLM windows via the API.

##### Changed:
- Inactive patterns and disabled output are crossed out in previews.
- Changing a pattern activates it.

##### Fixed:
- Refresh updates the screen list.
- Scroll wheel changes slider values.

See the [detailed changelog](CHANGELOG_FULL.md) for the full history.
