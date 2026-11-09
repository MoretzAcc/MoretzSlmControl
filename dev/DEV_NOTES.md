# Development notes

## Development commands

```bash
uv run moretzslmcontrol
uv run ruff check .
uv run python -m unittest discover -s tests
```

## Release preparation

- Version 0.3.6 integrates the reviewed PR #3 changes into `master`. Server and client distribution versions are synchronized.
- Release notes are recorded in the [changelog](CHANGELOG.md). Collect subsequent changes in a new Unreleased section until the next version is chosen.
- The current distribution version is recorded in `VERSION`. Historical changelog entries contain version labels that do not consistently match it; do not derive the next version from those labels alone.
- At release time, update `VERSION`, run `uv run python dev/sync_version.py`, and verify the resulting package metadata.
- Release validation commands are listed above. Offscreen checks cannot validate focus, compositor behavior, output fidelity, or native monitor discovery; record native desktop and physical SLM checks separately when performed.

## Completed in 0.3.5

- Reviewed and integrated PR #1 and PR #2, including regression tests for client/server contracts and monitor/session behavior.
- Replaced the tabbed controls with simultaneously visible pattern controls and adjustable UI scaling. All five previews follow the selected screen's aspect ratio; inactive patterns use a translucent, resolution-dependent `Off` overlay.
- Moved bits-per-channel information into physical monitor details. Magnification aligns with the other modification inputs.
- Added asynchronous pattern calculation with coalescing of pending edits and rejection of stale results.
- Synchronized remote Zernike and modification parameters with the UI. Remote shifts expand the local slider range when needed; slider max shift has no HEROS setter.
- Consolidated shared client/server phase and file helpers, bounded notebook preview sampling, and made pattern flip mapping explicit.
- Added output focus prevention and Windows Aero Peek exclusions. Native desktop behavior still needs platform testing.
- Added geometry/DPI change handling and session resizing. A changed output resolution resets patterns and optical parameters; unchanged geometry retains the current session.
- Retained HEROS connection functionality and configuration support while removing the unstable connection toggle from the UI.

## Completed in 0.3.6

- UI scaling preferences persist per user and optionally in exported configuration. Controls have a font-dependent minimum size; native SLM dimensions and pattern data are independent of UI scaling.
- The control window is resizable, its content can scroll, and the sidebar divider is draggable. The console fits into the space below Correction and Hologram without contributing size hints to the pattern layout.
- Windows WMI query failures use Qt metadata if no EDID was previously observed. A failure for an already observed screen reuses its last successful EDID; successful queries continue to refresh metadata and detect replaced monitors.
- Screen information receives more space relative to Associated monitors to keep HERO names readable.

## Open tasks

- Improve the current overlap between the Enable SLM output button and the output preview. Scaling down the preview is undesirable here, so an overlap can be a reasonable solution; the current implementation of that overlap needs improvement. Leave the UI unchanged until this design is revisited.
- Stabilize the HEROS connection toggle before exposing it in the user interface again.
- Consider a warning when a monitor reports more than 8 bits per channel. The value is displayed, but the software output remains 8-bit and currently has no such warning.
- Add more end-to-end usage examples; existing client examples are in [client/src/examples](../client/src/examples).
- Investigate intermittent Windows hotplug recovery reported during VM testing: an enabled output sometimes needs Refresh to reconnect. This is not fixed by the WMI fallback. Confirm on physical displays before changing topology handling.
- Distinguish identical monitor names in the sidebar with a connector or short screen identifier.

## Unreleased fixes

- The notched Pattern composition frame renders native Qt group-box sections and lets the active style position and paint its title. Rendering comparisons cover the locally available Windows and Fusion styles, larger fonts, and 100%/150%/200% display scaling; native Windows desktop rendering still needs verification.

## Known limitations and validation needs

- Native dimensions are derived from Qt geometry multiplied by device pixel ratio. Geometry/DPI signals and refresh trigger rescans, but aggressive or fractional OS scaling can still produce platform-specific problems. Verify both resolution changes and the resulting pattern reset on real hardware.
- Linux EDID-to-screen mapping depends on the desktop/compositor and needs further testing with multiple and mirrored monitors. Missing or duplicate metadata can prevent reliable identification.
- Screen IDs include host and monitor/connector information. They are intended to remain stable for an unchanged setup, but are not guaranteed hardware identifiers; moving ports or changing available metadata can change them.
- Verify output focus prevention on Linux and Windows and Aero Peek exclusions on Windows. These require a native desktop session.

## Future ideas

- Support output precision above 8 bits per channel.
- Optional REST API access.
