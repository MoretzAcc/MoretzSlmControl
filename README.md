# Moretz SLM Control

Desktop application for controlling spatial light modulator (SLM) displays.

> **AI notice:** This project was developed with AI assistance.

Tested on:

- Windows 11
- Fedora 44 KDE Wayland
- Ubuntu 24.04 GNOME Wayland

Using Spatial Light Modulators from:

- Holoeye
- Hamamatsu

## Requirements

- Python 3.14 or newer
- [uv](https://docs.astral.sh/uv/)

## Install and run

```bash
uv sync
uv run moretzslmcontrol
```

## Usage

1. Select a detected screen from the sidebar.
2. Enable its SLM window.
3. Load correction and hologram patterns from `.npy` or `.bmp` files.
4. Adjust the modification pattern and screen-specific settings as needed.

## HEROS integration

Each active SLM is exposed through [HEROS](https://pypi.org/project/heros/). This allows another process on the same computer, or a process on another device in the same network, to control the SLM without interacting with the GUI directly. Each screen has its own HERO name and console output.

## Development

```bash
uv run ruff check .
uv run mypy
```

## Notes

- The pattern coordinate origin is at the bottom left.
- Strong or fractional operating-system display scaling can affect the detected SLM resolution.

## Known issues

- Changing monitor settings while the application is running, such as display scaling, is not detected by Refresh.
- EDID detection is unstable on Linux. It has been tested with KDE Wayland and Ubuntu GNOME Wayland.
