
Run Program
```bash
uv run moretzslmcontrol
```

Run unit tests:
```bash
uv run python -m unittest discover -s tests
```

### TODO Bugs / Issues

- Toggle SLM window should have true false argument
- when slm window is enabled it gains focus (at least on linux) i dont want that

- Windows Aero Peek, one idea to fix is in anti_aero_peak.py
- Control Window may be hidden behind slm display windows -> stupid people can hardlock themselves
    - This can happen through activation of the display over the control software
        - solution 1: prevent activation of display on primary monitor
        - solution 2: prevent activation of display on the monitor where the mouse is currently located
    - This can happen via moving the control window to a different monitor
        - solution: detect movement. After movement if on a monitor with active display, teleport back onto primary monitor / monitor with no active display
        - solution: detect movement. After movement if on a monitor with active display, disable the display on that monitor


### TODO Tasks

- Sending a pattern via heros should enable the screen by default (should it?)
- button to reset session into null state
- Connection via Heros toggleable
- speed up program
    - speed up the modification pattern generation
    - speed up the hologram generation
    - remove freeze on parameter change
- remove duplicate code from client and server
- make plotHologram faster
- Method hologram_manager.py -> _set_pattern_flip stinks
- Show bitdepth in the UI
    - Detect if SLM bitdepth is > 8, and warn the user.

### TODO Future Ideas

- Support SLM with different bit depth than 8
- Connection via Rest Api toggleable

### TODO put into README

- Examples
- Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port

### Known Issues - Won't Fix

- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.
- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.

# Changelog

### 26-09-09

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