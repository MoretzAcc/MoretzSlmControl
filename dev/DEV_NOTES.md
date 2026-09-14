
Run Program
```bash
uv run moretzslmcontrol
```

Run unit tests:
```bash
uv run python -m unittest discover -s tests
```

### TODO Bugs / Issues

- when slm window is enabled it gains focus (at least on linux) i dont want that
- Windows Aero Peek, one idea to fix is in anti_aero_peak.py
- Control Window may be hidden behind slm display windows -> stupid people can hardlock themselves
    - This can happen through activation of the display over the control software
        - solution 1: prevent activation of display on primary monitor
        - solution 2: prevent activation of display on the monitor where the mouse is currently located
    - This can happen via moving the control window to a different monitor
        - solution: detect movement. After movement if on a monitor with active display, teleport back onto primary monitor / monitor with no active display
        - solution: detect movement. After movement if on a monitor with active display, disable the display on that monitor
    - Fix: When pressing SLM Window Enable Button check if associated monitors contains mouse.getMonitor. 
      - If yes, make a popup and ask for confirmation (add a comment that this popup appeared because mouse click / manual open, it would not appear when using heros)

### TODO Tasks

- Rework design of the enable / disable window button
- button to reset session into null state
  - with popup to confirm
- Connection via Heros toggleable
- speed up program
    - speed up the modification pattern generation
    - speed up the hologram generation
    - remove freeze on parameter change
- remove duplicate code from client and server
- make plotHologram faster
- Method hologram_manager.py -> _set_pattern_flip stinks
- Show bitdepth in the UI
    - Detect if SLM bitdepth is > 8, and warn the user taht this is not supported by this software.
- Replace crossout by text "DIsabled" or "Off"
  - Black text auf white background, text and background are slightly opaque, has to be calculated

### TODO Future Ideas

- Allow saving a session (for one SLM display)
  - Save current state to json
    - save all holograms
    - save settings
    - save header
      - json meta data
        - program version (= json version)
        - when saved
      - screen metadata
        - resolution for verification
        - other info jsut for information
  - Load session from json 
    - respect defaults if value is not included
    - throw warning if version is not identical
    - throw error if resolution does not match
- Support SLM with different bit depth than 8
- Connection via Rest Api toggleable

### TODO put into README

- Examples
- Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port
- Explain why Screen and Monitor are different and have a manyto one relation

### Known Issues - Won't Fix

- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.
- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.