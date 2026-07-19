

```bash
uv run moretzslmcontrol
```


### TODO 
- Connection via Heros toggleable
- Connection via Rest Api toggleable
- Default Hologram that displays 0, 255 with a text printed on top, and in the center is a phase vortex to generate donut
- Better UI
  - Preview of active hologram
  - UI Panel for any Display
    - Button to directly upload specific hologram from file (without need of network connection)
    - Button: Flip X / Y Hologram
    - Slider and Textbox for Shift in X,y,z
    - Export/Import Configuration
    - Small Console to see Logs (also printed to file)
- Support SLM with different bit depth than 8
- Aggressive Typing
- Generate better heros name. Deterministic, but no duplicates: Hash of display info + computer info into 8 digit number

### TODO in README
Examples

Usage of AI
- Backend was created without AI
- User Interface was created with the help of AI

Coordinate system... where is (0,0)? (Old comment: Flipped y Axis -> 0,0 is bottom left)

Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port

# Known Bugs

- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.

- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.