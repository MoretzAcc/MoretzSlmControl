# Fork changelog

## Versioning

This fork retains the complete upstream version, including its optional `.postN` suffix, and adds a PEP 440 local version: `UPSTREAM+moretzai.N`.

Example: upstream `0.3.4.post2` becomes `0.3.4.post2+moretzai.1`. Each independently committed fork TODO increments N. Upstream owns the third release number and `.postN` (small follow-up fixes/documentation); the fork does not pretend its changes are upstream releases. When adopting a new upstream release, retain that new upstream version and restart the fork counter at 1. Server and standalone client versions stay synchronized through `VERSION` and `dev/sync_version.py`. Local versions are intended for Git/local installation, not publication to public PyPI.

Every TODO entry records implementation, review, and actual validation. Windows-only behavior and physical SLM capabilities must be distinguished from Linux/simulated validation. Future ideas (>8-bit optical output and an additional REST API) remain separate unless explicitly brought into scope.

## Work items

- F01: Missing-EDID screen identity and collision protection.
- F02: Coalesced Zernike calculations, latest desired state, stale-result invalidation.
- F03: Coalesced modification calculations.
- F04: Immediate slider text feedback, including wheel/keyboard.
- F05: Responsive, readable UI and input/status feedback.
- F06: Resolution/DPR-change lifecycle and stable reconnects.
- F07: Output focus preservation.
- F08: Windows Aero Peek exclusion.
- F09: Output enable/disable action design.
- F10: Toggleable HEROS connection, configuration persistence.
- F11: Deduplicate standalone client/server helpers without GUI dependencies.
- F12: Faster plotting/previews and measured validation.
- F13: Simplify pattern-flip handling.
- F14: Display bit-depth support and truthful capability warnings.
- F15: Replace crossed-out previews with Off overlays.
- F16: Examples, identity/monitor terminology, refresh/scaling documentation and TODO disposition.
- F17: Final integration matrix, screenshots, and updated review.

## 0.3.4.post2+moretzai.0 — Review baseline

- Implementation: Preserve the initial review, screenshots, dummy-monitor lab and reproducible defects; establish fork versioning and individual work-item tracking.
- Review: Production application source remains unchanged; historical results retain failing expectations rather than claiming fixes.
- Testing: Initial 15 unit tests and Ruff pass; baseline real-Qt matrix documents layout, queue, stale-state, identity, focus and mode-change defects.

## 0.3.4.post2+moretzai.1 — F01: Keep missing-EDID monitor identities distinct

- Implementation: Use stable connector fallback IDs, deterministic EDID ordering, and refuse duplicate record overwrites.
- Review: Verified geometry/DPR changes do not change a connector UID; EDID-backed identities preserve their existing inputs.
- Testing: Regression covers distinct missing-EDID connectors and stable IDs across mode/position/DPR changes. Full unittest suite and Ruff passed before commit.

## 0.3.4.post2+moretzai.2 — F02: Coalesce Zernike work and reject obsolete desired states

- Implementation: Keep one running job and one replaceable latest snapshot per screen; invalidate a job even when returning to the applied value; discard queued work on reset/close.
- Review: Reviewed thread/Qt boundaries, stale revisions, reset generations and completion ordering. The original frame stays visible until the newest result is accepted.
- Testing: Deterministic event-gated Qt regressions prove first/latest-only execution and A-B-A correctness without timing assumptions. Full unittest suite and Ruff passed before commit.
