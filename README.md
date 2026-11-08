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
git clone https://github.com/MoretzAccAi/MoretzSlmControl.git
cd MoretzSlmControl
uv sync --locked
uv run moretzslmcontrol
```

This fork installs its matching standalone client from the `client/` directory through uv. Keep both distributions together when building/installing wheels. Fork versions retain the upstream release plus `+moretzai.N`; see [CHANGELOG-FORK.md](CHANGELOG-FORK.md) for per-TODO implementation, review and validation.

## Usage

1. Select a detected screen from the sidebar.
2. Enable its SLM output. The control keeps keyboard focus; the native output remains fullscreen.
3. Load correction and hologram patterns from `.npy` or `.bmp` files.
4. Use the Correction, Hologram, Zernike and Modification tabs. Numeric controls remain readable in small windows; scroll the detail pane when necessary.
5. Slider values update while dragging. Pattern calculation runs asynchronously and combines rapid edits into the newest desired state.
6. Enable or disable the HEROS connection in the Screen tab. This leaves local output and patterns intact. Export configuration to preserve the connection preference (v2 files; legacy v1 remains readable).

## HEROS integration

Each active SLM is exposed through [HEROS](https://pypi.org/project/heros/). This allows another process on the same computer, or a process on another device in the same network, to control the SLM without interacting
with the GUI directly. Each screen has its own HERO name and console output.

The lightweight client is available as a separate package and supports Python 3.11 or newer.
To import the client in any of your projects:

Install the client using pip or conda:

```bash
python -m pip install "git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
```

Using uv:

```bash
uv add "git+https://github.com/MoretzAcc/MoretzSlmControl.git#subdirectory=client"
```

How to use it is described in /client/README.md.

## Development

```bash
uv run ruff check .
uv run mypy
uv run python -m unittest discover -s tests
```

## Pattern examples

Create an exactly sized float32 phase ramp (dimensions are height, width):

```python
import numpy as np

height, width = 1080, 1920  # Use the selected screen's native resolution.
phase = np.broadcast_to(np.linspace(-np.pi, np.pi, width, endpoint=False,
                                   dtype=np.float32), (height, width)).copy()
np.save("ramp.npy", phase)
```

Load `ramp.npy` from the Hologram tab, toggle components, and inspect the preview before enabling the intended output. NPY inputs contain phase in radians; BMP inputs are grayscale byte values. The coordinate origin is at the bottom left. Export/import configurations preserve imported patterns and flip states; applying a different-resolution configuration prompts to import settings only.

Remote access (enable the screen's HEROS connection first):

```python
from moretzslmclient import SlmHeroApi, discover_slm_heros, importNpyHologram

names = discover_slm_heros()
if not names:
    raise RuntimeError("Enable a HEROS connection in the desktop application first")
with SlmHeroApi(names[0]) as slm:  # Choose the intended screen explicitly in a real setup.
    slm.setHologramPattern(importNpyHologram("ramp.npy"))
```

See [client/README.md](client/README.md) for client installation and previews.

## Screens, monitors and persistent identity

A screen/display is a software output. A monitor is a physical device; mirrored monitors can share one screen, so the relationship is many monitors to one screen. An output window is one native fullscreen window associated with a screen.

The screen UID and derived HERO name combine the host ID and associated monitor EDID/connector identifiers, manufacture information and serials. EDIDs are sorted before hashing. On the same host, monitor and port these should remain stable across mode/position changes. Without EDID, the host and Qt connector name identify the output; changing its connector name may change the UID. Missing/duplicated serials and firmware/EDID changes limit hardware identity guarantees. Duplicate IDs are detected rather than silently overwriting another record.

## Resolution, scaling and bit depth

The application observes Qt screen geometry/DPI changes and supports Refresh. When native pixel dimensions change, the existing session retains its identity and connection preference but resets all pixel patterns, calculated grids and pending results, with a console warning. Reload/reapply patterns for the new dimensions; no old buffer is silently stretched. Disconnect/reconnect retains per-screen sessions and their enable state when identity remains stable.

Native dimensions use Qt geometry multiplied by device pixel ratio. Integer-resolution changes are integration-tested; fractional/aggressive scaling and compositor-specific mappings still need hardware validation. Control-window layout does not define SLM pixel geometry.

Software output is **8-bit grayscale (256 levels)**. The Screen tab reports digital EDID 1.4 input bits/channel where available and warns above eight bits. Advertised input depth is neither the currently active transport depth nor optical phase precision; unknown capabilities remain Unknown. Higher-bit-depth optical output is not implemented.

## Testing and remaining platform limits

- [Virtual monitor lab](dev/review/README.md): isolated Xorg dummy outputs, portrait/full-HD/ultrawide/4K geometries, hotplug, screenshots and five-second calculation workloads.
- [Fork changelog](CHANGELOG-FORK.md): individual TODO changes and actual review/test evidence.
- [Developer notes](dev/DEV_NOTES.md): completed work, remaining native-platform validation and future ideas.
- The initial review and failing baseline are preserved under `dev/review/results/`; newer evidence is separate under `dev/review/fork-results/`.
- Windows output requests exclusion from taskbar/desktop Aero Peek. API contracts are tested using native-call mocks on Linux; visual verification on Windows remains required.
- Physical SLM phase response, transport precision and refresh timing are not established by virtual monitors.
