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
git pull <your preferred method of pulling>
uv sync
uv run moretzslmcontrol
```

## Usage

1. Select a detected screen from the sidebar.
2. Enable its SLM window.
3. Load correction and hologram patterns from `.npy` or `.bmp` files.
4. Adjust the modification pattern and screen-specific settings as needed.

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

## Notes

- The pattern coordinate origin is at the bottom left.
- Display, Screen and Monitor are not synonymous:
  - Display and Screen can be treated as synonymous. There are defined in Software.
  - Monitors are the hardware connected to the PC. Through screen mirroring, multiple monitors can show the same Screen. 
- Screens and Monitors do not have a safe unique ID.
  - This software generates a unique ID for each screen based on:
    - Display Name
    - Serial Numbers of all Monitors showing this screen (empty for many devices)
    - Manufacturer Date of all Monitors showing this screen
    - OS Identifies of all Monitors showing this screen (related to the connected Port)
  - With this, it is impossible to have two screens with the same UID connected at the same time. 

## Known issues

- Changing monitor settings while the application is running, such as display scaling, is not detected by refresh.
- This software is supposed to be able to deal with OS-sided display scaling. However, for very strong (e.g. 20%, 500%) or fractional scaling (e.g. 85%), some issues may appear.
- EDID detection is unstable on Linux. It has been tested with KDE Wayland and Ubuntu GNOME Wayland. It works in most cases, but might break for cases where multiple monitors or monitor duplication is enabled. However, a
  fail would be noticeable immediately.