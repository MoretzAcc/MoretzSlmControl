
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

### TODO Tasks

- ! Design: Rework design of the enable / disable window button
- button to reset session into null state
  - with popup to confirm
- Connection via Heros toggleable
- speed up program
    - speed up the modification pattern generation
    - speed up the hologram generation
    - remove freeze on parameter change
    - precalculate default modification pattern and zernike pattern on activation of the slm, in the background such that it is non blocking
      - show a loading indicator somewhere
- remove duplicate code from client and server
- make plotHologram faster
- Method hologram_manager.py -> _set_pattern_flip stinks
- ! Show bitdepth in the UI
    - Detect if SLM bitdepth is > 8, and warn the user taht this is not supported by this software.
- ! Design: Replace crossout by text "Disabled" or "Off"
  - Black text auf white background, text and background are slightly opaque, has to be calculated

### TODO Future Ideas
- Allow saving a session (for one SLM display)
  - Ideas: Save current state to json / hdf5
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
- README: "Changing monitor settings while the application is running, such as display scaling, is not detected by refresh." might be wrong

### TODO put into README

- Examples
- Monitor UID, Herosname should be the same for a given combination of pc + monitor + used port
- Explain why Screen and Monitor are different and have a manyto one relation

### Known Issues - Won't Fix

- Device Height x Width are calculated as geometry Height / Width times devicePixelRatio (induced by scaling from OS settings).
  → Aggressive scaling or fractional scaling can cause problems here.
- Changing monitor settings while program is active (e.g. changing scale) will not be detected even when pressing refresh button.

### Temp:

1. Config saver. Es geht darum, dass es möglichst simple zu verstehen ist. Daher export und import button reichen.
   Es sollen möglichst alle metadaten darin gespeichert sein, damit man das nachträglich lesen kann. json wäre bevorzugt, wär natürlich gut, wenn die aktuellen holograms da auch drinne sind, überleg dir ob das technisch einfach ist, ich will keinen Rieseneingriff. Beim import einer config soll nur das nötigste gecheckt werden. d.h. ob die slm größe identisch sind (ich glaube der rest ist kompatibel). Falls größe nicht identisch ist, muss ein popup kommen was darüber benachrichtigt und um bestätigung bittet, die config trotzdem zu applien, in dem Fall werden dann natürlich keine patterns importiert, sondern nur die anderen parameter.
   Außerdem in die AGENTS.md rein, dass die Config bei anderen änderungen nicht vergessen werden soll.

2. reset button / button um bereits / aus versehen aktivierte sessions in den nicht-initialisierten zustand zu versetzen. Mit bestätigungspopup. Möglichst minimaler eingriff

3. Speed up programm
   Es gibt zu viele laggs / initialisierung ist blocking implementiert. Ich hätte gerne dass zuerst nach speedups geschaut wird. 
   Danach sollen die initialisierungen noch non-blocking gemacht werden, wichtig ist ein loading indicator, damit das nicht so aussieht als wärs kaputt.