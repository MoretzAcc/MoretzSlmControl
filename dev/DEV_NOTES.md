```bash
uv run moretzslmcontrol
```

### TODO Bugs / Issues
- Error message is green (Windows) "Error importing base aberration: cannot identify image file 'C:\\Users\\morit\\Downloads\\SteelSeriesGG112.0.0Setup.exe.bmp'"
- Windows Aero Peek, one idea to fix is in anti_aero_peak.py
- Control Window may be hidden behind slm display windows -> stupid people can hardlock themselves -> solution: prevent activation of display on primary monitor

### TODO Tasks
- log that session initialized, log that heros activated
- button to reset session into null state
- Connection via Heros toggleable
- Default Hologram that displays 0, 255 with a text printed on top, and in the center is a phase vortex to generate donut
- allow fractional values using slider using for modification pattern
- speed up the modification pattern generation
- remove duplicate code from client and server
- make plotHologram faster

### TODO Future Ideas 
- Support SLM with different bit depth than 8
- Connection via Rest Api toggleable

### TODO put into README
- Examples
- Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port

# Known Issues - Won't Fix
- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.
- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.