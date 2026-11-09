# Moretz SLM Control

Desktop application for controlling spatial light modulator (SLM) displays.

> **AI notice:** This project was developed with AI assistance.

Tested on Operating Systems:

- Windows 11
- Fedora 44 KDE Wayland
- Ubuntu 24.04 GNOME Wayland

Tested using Spatial Light Modulators from:

- Holoeye
- Hamamatsu

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)

## Install and run

```bash
git clone https://github.com/MoretzAcc/MoretzSlmControl.git
cd MoretzSlmControl
uv sync
uv run moretzslmcontrol
```

## Usage

1. Select a detected screen from the sidebar.
2. Enable its SLM output. The control keeps keyboard focus; the native output remains fullscreen.
3. Load correction and hologram patterns from `.npy` or `.bmp` files.
4. Edit the Correction, Hologram, Zernike and Modification controls alongside the output preview. Use **Scale UI** in the sidebar or Ctrl+- / Ctrl++ to adjust the global interface scale. The gear button opens live **UI settings** with independent relative factors for font size, UI elements and previews. Each effective factor is the global scale multiplied by its relative factor. New profiles start at 100%; larger controls remain accessible through the scrollable content area.
5. Slider values update while dragging. Pattern calculation runs asynchronously and combines rapid edits into the newest desired state.
6. Export configuration to save the session settings and patterns, or import a saved configuration. Current exports use format v2; legacy v1 remains readable.

UI preferences are saved automatically to `~/.config/moretzslmcontrol/settings.json`
(`C:\Users\<user>\.config\moretzslmcontrol\settings.json` on Windows), and restored at
startup. A missing file is created with default values; invalid settings are backed
up before defaults are written. **Restore Defaults** in UI settings resets all four
factors to 100%. Scaling changes previews and controls, preserving native SLM output
dimensions and pattern data. Buttons and checkboxes keep a minimum size that fits
their text when the font factor is larger than the element factor.

Drag the divider beside **Screens** to resize the sidebar. UI scaling preserves
the sidebar width; its contents scroll if they need more room.

Configuration exports also include the optional `controls.ui` factors. Importing
them applies and saves the UI preferences immediately. Older v1/v2 configurations
without that field retain the current UI preferences.

## HEROS integration

Each active SLM is exposed through [HEROS](https://pypi.org/project/heros/). This allows another process on the same computer, or a process on another device in the same network, to control the SLM without interacting
with the GUI directly. Each screen has its own HERO name and console output.

The connection toggle is temporarily hidden while its behavior is stabilized. HEROS functionality and the saved connection preference remain supported. Remote Zernike and modification setters update the desktop controls; shifts outside the current slider range expand it automatically.

The lightweight client is available as a separate package and supports Python 3.11 or newer.
To import the client in any of your projects:

Install the client using pip:

```bash
python -m pip install "git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
```

Using uv:

```bash
uv add "git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
```

See the [client README](client/README.md) for examples and parameter units. Use a client from the same branch or release as the server when trying unreleased API additions.

## Development

```bash
uv run ruff check .
uv run mypy
uv run python -m unittest discover -s tests
```

## Notes

- The pattern coordinate origin is at the bottom left.
- A Screen (or Display) is a software output; a Monitor is physical hardware. Screen mirroring can make multiple monitors show one screen. Bits per channel are reported in each monitor's details when available; SLM output currently uses 8-bit values.
- Screen IDs and HERO names incorporate host, display, monitor metadata and connector information. They are intended to stay stable for an unchanged computer/monitor/port combination, but missing or duplicate metadata prevents a uniqueness guarantee. Screens without EDID use a host/Qt connector fallback. Changing ports or available metadata can change an ID.
- Geometry/DPI changes trigger a rescan. If the detected output resolution changes, patterns and optical parameters reset to match the new dimensions. Export configuration before changing display settings if you need to preserve the session.

## Known issues

- This software is supposed to be able to deal with OS-sided display scaling. However, for very strong (e.g. 20%, 500%) or fractional scaling (e.g. 85%), some issues may appear.
- Linux EDID detection has been tested with KDE Wayland and Ubuntu GNOME Wayland, but monitor mapping can be unreliable with multiple or mirrored monitors. Check the detected monitor details before enabling output.

See the [changelog](dev/CHANGELOG.md) for release changes and [development notes](dev/DEV_NOTES.md) for remaining work and platform validation needs.
