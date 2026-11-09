# Fork changelog

## 0.3.5+moretzai.5 — 2026-11-09

- Added a draggable horizontal divider for the screen sidebar. Its width stays
  independent of UI scaling; sidebar contents scroll when necessary.
- Removed the nonfunctional divider above the console, including its resize cursor.
  Pattern composition remains at content height and the console uses spare space.

## 0.3.5+moretzai.4 — 2026-11-09

- Kept Pattern composition at its content height, recalculating when fonts or
  previews change. Surplus splitter space goes to the console instead of adding
  blank space beneath the pattern controls.
- Made all four centered pattern-column headings bold.
- Removed the redundant output-status text above the applied preview; the preview
  and output button continue to communicate output state.

## 0.3.5+moretzai.3 — 2026-11-09

- Centered pattern titles and previews in their columns, including the applied-output preview.
- Kept pattern titles, previews and controls at the top instead of stretching the
  preview row and distributing surplus height around the titles.
- Made composition plus signs bold and 1.5 times the normal font size, retaining
  the global and relative font scaling behavior.

## 0.3.5+moretzai.2 — 2026-11-09

- Aligned associated-monitor headings and metadata to the top of each card, with
  bold left-aligned headings and unused space below the metadata.
- Replaced the scale row with `Scale UI: xx% + -` and a gear button. Added a
  modeless settings window with immediate, independent font/element/preview factors.
- Global scaling multiplies all three relative factors. Removed automatic startup
  font reduction; new profiles use 100%. Added scrollable content and retained
  native SLM dimensions and output bytes when UI preferences change.
- Persisted all four factors atomically in per-user settings.json, creating defaults
  on first run and backing up invalid files. Optional controls.ui configuration
  exports/imports include these factors; legacy files keep existing UI preferences.
- Validation: 64 unittest tests successful with one platform skip; native Windows
  UI checks confirmed live font/preview changes, persistence, top-aligned headings,
  and unchanged output bytes. Linux native GUI behavior was not verified.

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
