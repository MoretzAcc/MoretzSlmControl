```bash
uv run moretzslmcontrol
```

### TODO Bugs / Issues
- Error message is green (Windows) "Error importing base aberration: cannot identify image file 'C:\\Users\\morit\\Downloads\\SteelSeriesGG112.0.0Setup.exe.bmp'"
- Windows Aero Peek, one idea to fix is in anti_aero_peak.py
- Control Window may be hidden behind slm display windows -> stupid people can hardlock themselves 
  - This can happen through activation of the display over the control software
    - solution 1: prevent activation of display on primary monitor
    - solution 2: prevent activation of display on the monitor where the mouse is currently located
  - This can happen via moving the control window to a different monitor
    - solution: detect movement. After movement if on a monitor with active display, teleport back onto primary monitor / monitor with no active display
    - solution: detect movement. After movement if on a monitor with active display, disable the display on that monitor

### TODO Tasks
- log that session initialized, log that heros activated
- button to reset session into null state
- Connection via Heros toggleable
- allow fractional values using slider using for modification pattern
- speed up program
  - speed up the modification pattern generation
  - speed up the hologram generation
- remove duplicate code from client and server
- make plotHologram faster
- Default Hologram that displays 0, 255 with a text printed on top, and in the center is a phase vortex to generate donut
- Expose disabling of SLM display into api

### TODO Future Ideas 
- Support SLM with different bit depth than 8
  - Quick solution: Detect if SLM bitdepth is > 8, and warn the user. Show bitdepth in the UI.
- Connection via Rest Api toggleable

### TODO put into README
- Examples
- Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port

# Known Issues - Won't Fix
- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.
- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.