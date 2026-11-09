# PR #3 review

Date: 2026-11-09. Base: upstream `master` at `ebfcd42` (0.3.5).
Reviewed PR head: `c25041026d7165f2fc11d9e0eb2e03d61a29ac10`.
Integration branch: `review/pr-3`. No application fixes were applied during this review.

## Assessment

The Windows startup fallback is useful, and the persistent scaling settings have
validation, atomic saves and backwards-compatible optional configuration fields.
The UI changes preserve the existing remote optical setters and hidden HEROS toggle.
However, three reproducible issues below should be resolved or explicitly accepted
before integrating this branch into the release branch.

## Findings

### R1 — P1: Transient EDID failure detaches the existing output session

Location: `src/moretzslmcontrol/monitor_stuff/platform/windows.py`,
`WindowsPlatformAdapter.get_screen_edids`, interacting with
`PlatformAdapter.describe_screen` and `MonitorManager.rescan_screens`.

The new COM exception handler returns an empty EDID list. If this happens after a
successful scan, the same Qt screen gets a different UID: one identity uses EDID
metadata, the other uses the no-EDID connector fallback. The manager marks the old
record disconnected and detaches its existing output session, although the Qt
screen is still present. A new record does not inherit the existing session or its
HERO name. Recovery to EDID metadata changes the identity again.

Reproduced through the real shared descriptor and rescan logic with one mocked
screen/provider: change the provider from a valid EDID to an empty list without
removing the screen. The old record becomes disconnected and `detach_screen` is
called. No Windows COM call or physical hotplug was needed for this reproduction.
The identity scheme predates this PR; the new catch now takes this path instead of
terminating on the COM error. Permanent EDID unavailability from startup works as
intended, but transition behavior is not covered by the PR's Windows fallback test.

Suggested direction: preserve the identity/session of an already observed Qt
screen across temporary metadata failures. Also test the inverse transition from
fallback metadata to a recovered EDID without moving output to the wrong monitor.

Reproduction: `Pr3ReviewTest.test_temporary_edid_failure_keeps_the_current_output_attached`.

### R2 — P2: Independent font/element factors clip controls

Location: `MainWindow._apply_ui_scale` and the fixed-size sidebar scale buttons.

The settings permit font size and element size to vary independently, but button
maximum dimensions are scaled only by the element factor. With global 100%, font
200%, and elements 50%, the scale buttons are 13x13 pixels while their font line
height is 33 pixels in the offscreen Linux environment. Their text/gear is clipped.
File-pattern flip checkboxes also show truncated labels in that configuration.
Scrolling cannot recover content clipped inside a fixed-size widget.

Numeric fields have a font-height safeguard; other controls do not. Keep button
bounds large enough for their font/style content, or constrain the combinations
and explain the constraint. This affects permitted settings, not native SLM data.

Reproduction: `Pr3ReviewTest.test_large_fonts_keep_scaling_buttons_readable`.

### R3 — P2: Existing tests read and overwrite the real UI preference file

Location: `tests/test_calculation_scheduling.py` and
`tests/test_remote_parameters.py`, whose setup still constructs `MainWindow`
without the new `settings_path`; persistence is triggered by
`MainWindow._change_ui_scale` / `_set_ui_settings`.

Those tests now load the developer's actual saved settings. The scheduling tests
also write changes back. The default suite can therefore modify a user's profile
and its results depend on that profile. The new UI-specific tests correctly use
temporary paths, but the older tests were not migrated.

Reproduced safely with the default path redirected to a temporary 300% profile:
`test_ui_scale_round_trip_preserves_font_size` fails and leaves global scale at
295%. At the upper bound, the increment clamps before the decrement, so its
roundtrip assumption is false. No real user settings were changed in this review.

Give every MainWindow test an isolated temporary settings path and an explicit
starting profile. Test clamping separately from scale-roundtrip behavior.

Reproduction: `Pr3ReviewTest.test_existing_scheduling_test_does_not_depend_on_or_modify_user_preferences`.

## Scope and integration observations

- The PR changes 50 files, with 4,040 insertions and 76 deletions before the review
  additions. Much of this is Windows review tooling and historical JSON/screenshots
  (the results directory occupies about 472 KiB on disk). The production changes
  are substantially smaller. The evidence is useful, but it should be an explicit
  scope choice rather than an incidental part of a UI/startup fix.
- `VERSION`, both package manifests and both lockfiles become
  `0.3.5+moretzai.6`. `AGENTS.md` also acquires a permanent fork-version policy and
  `CHANGELOG-FORK.md`. These describe the contributor's fork; upstream release
  versioning and changelog placement need a deliberate decision before merging.
  They were preserved verbatim on this review branch.
- The embedded console adds a custom-painted notched frame and manual child
  positioning. The supplied console layout tests pass for their covered cases;
  no console disappearance was reproduced in the additional scale sweep. This
  remains a larger design/maintenance change than the Windows startup fix.
- Historical Windows evidence reports intermittent hotplug recovery failures
  (two of three recorded cycles) and ambiguous labels for identical monitors.
  These are documented pre-existing findings, not newly reproduced regressions
  from this review. The PR does not fix that hotplug behavior. Some earlier UI
  findings in that report were addressed by later PR commits, so the historical
  report is not a current acceptance result for the final PR head.

## Validation

- `uv sync --locked --offline`: successful; installed both matching fork packages.
- `uv run --locked --offline ruff check .`: passed.
- Original suite: 67 tests, no failures, one Windows-only test skipped on Linux.
  The shared default settings path was patched to a temporary file for the run.
- Added review checks: three tests, all fail as expected for R1/R2/R3; these are
  deliberately ordinary failing tests, not skips or expected-failure decorators.
  The full combined suite therefore is not green.
- Combined isolated suite: 70 tests, exactly the three review failures, no errors,
  one Windows-only skip (66 passing tests).
- Offscreen application entrypoint: started and shut down normally (exit 0), using
  a temporary settings path. Missing offscreen connector EDID is expected.
- Additional visual/geometry probes covered defaults, font 150% and 200%, global
  25% and 300%, and opposing font/element factors. Preview surfaces retained their
  configured proportions. R2 was checked visually and by widget/font geometry.
- No native Windows session, physical SLM, real monitor hotplug, mixed-DPI desktop,
  or native Linux compositor rendering was verified here. The Windows artifacts
  in the PR are contributor-provided evidence, not tests rerun on this host.

Run just the added reproductions:

```bash
uv run python -m unittest discover -s tests -p test_pr3_review.py
```

The full suite includes them automatically. Until R3 is fixed, redirect or mock
`moretzslmcontrol.userinterface.main_window.ui_settings_path` to a temporary file
when running the older tests, to avoid touching personal preferences.
