# UI review validation

The UI uses two Zernike columns: defocus / primary spherical, astigmatism 0 / 45, coma 0 / 90, trefoil 0 / 90, and second-order astigmatism 0 / 45. Shared grid rows give all four pattern previews equal height; a post-layout pixel adjustment removes column rounding differences. The previews grow into the available area.

Widget minimum dimensions and layout margins/spacing use a 0.9 reference factor independently of the font. Font changes copy the saved QFont, fixing cumulative shrinkage during repeated scale changes.

## Verification

- Linux X11: 1280x800 and 1920x1080; equal previews (239x178 and 301x208 respectively), no checked input/button/console outside the window, and identical font size before/after scale round trips.
- Native Windows 11 LTSC: 1280x800; four previews exactly 246x87, no checked input/button/console outside the window, stable font round trip. Full HD was not tested natively on Windows in this run.
- Ruff and all 42 Linux unittest checks pass, including the font-scale round-trip regression.
- Screenshots show synthetic phase ramps to make preview extents visible. No physical SLM was used.

The Windows VM WMI monitor provider returns 0x8004100c. The visual harness supplies an empty EDID list only on Windows; the main window, native Qt plugin, monitor manager, and layout code remain real. This verifies GUI behavior, not WMI monitor enumeration.

`check_ui.py OUTPUT_DIR` is run inside the project environment on the chosen display. JSON results and PNG screenshots accompany this report. The Windows guest is shut down after the test.
