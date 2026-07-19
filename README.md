

```bash
uv run moretzslmcontrol
```


### TODO 
- Connection via Heros toggleable
- Connection via Rest Api toggleable
- Default Hologram that displays 0, 255 with a text printed on top, and in the center is a phase vortex to generate donut
- Support SLM with different bit depth than 8
- Aggressive Typing

### TODO in README
Examples

Usage of AI
- Big help of AI

Coordinate system: (0,0) is in bottom left

Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port

# Known Bugs

- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.

- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.