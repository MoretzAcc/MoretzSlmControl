# Developer notes

Run the application with `uv run moretzslmcontrol`; run `uv run ruff check .` and `uv run python -m unittest discover -s tests`.

## Implemented fork TODOs

Each item has its own commit and implementation/review/testing entry in [CHANGELOG-FORK.md](../CHANGELOG-FORK.md).

- F01: Distinct/stable missing-EDID identities and collision detection.
- F02/F03: Coalesced Zernike/modification work; obsolete-state and reset protection.
- F04: Immediate slider text and debounced keyboard/wheel calculations.
- F05: Readable, scrollable numeric forms, pattern tabs and metadata tabs.
- F06: Geometry/DPI observation and explicit native-buffer resets.
- F07: No output-window activation or repeated frame focus stealing.
- F08: DWM Aero Peek exclusion implemented; native Windows visual check pending.
- F09: Theme-native enable/disable action separate from output status.
- F10: Toggleable HEROS registration and backward-compatible configuration persistence.
- F11: Client-owned shared file/numerical helpers; no GUI dependency or import-time network observer.
- F12: Bounded GUI/notebook previews, full-resolution opt-out and 4K benchmark.
- F13: Explicit validated flip controls with reversible semantics.
- F14: Software depth and EDID input capability reporting, including >8-bit warnings.
- F15: Translucent white Off overlay with dark text, applied only to previews.
- F16: Usage/examples, screen-vs-monitor terminology, stable identity limits and corrected refresh/scaling documentation.
- F17: Strict integration runner, current screenshots and 123 passing geometry/runtime expectations.
- F06a: Stable observed identity even when EDID disappears during physical unplug.
- F18: Prompt SIGINT/SIGTERM handling while the Qt event loop is idle.

## Validation still requiring another environment

- Windows/Aero Peek: test taskbar and Show Desktop with an actual optical output. Linux tests cover API arguments/failure handling, not Windows composition behavior.
- Physical SLM hardware: verify optical phase calibration, active link precision, refresh timing and EDID completeness.
- Fractional/aggressive DPI scaling: verify native pixel mapping on real Wayland/Windows hardware. Control UI remains scrollable, but no virtual matrix can establish optical correctness.

## Future ideas (outside this requested implementation)

- Native optical output with more than eight bits.
- A separately toggleable REST API.

## Repeatable integration lab

Read [review/README.md](review/README.md) before starting the isolated Xorg dummy display. Preserve the initial failing baseline in `review/results/`; save current verification to `review/fork-results/`.
