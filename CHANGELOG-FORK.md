# Fork changelog

## 0.3.5+moretzai.1 — 2026-11-09

- Synchronized fork master with upstream 0.3.5, preserving the fork's merge history.
- Fixed Windows startup when WMI EDID enumeration raises a COM error, using the
  existing Qt screen fallback. Added a native-Windows regression test.
- Added native Windows display inventory, resolution-matrix and hotplug review
  tooling and retained measured results and selected screenshots.
- Reviewed seven resolutions with three native screens, including actual local
  HEROS client control and live resolution changes. Matrix: 113/116 checks passed;
  three control-window-fit failures remain. Two of three hotplug cycles missed
  one output; a manual refresh restored it in the diagnostic repeat. These
  outstanding findings are documented.
- Verification: Ruff passed; 55 unittest tests successful, one Windows skip.
- Detailed findings and remaining validation limits: dev/windows-review/REVIEW.md.
