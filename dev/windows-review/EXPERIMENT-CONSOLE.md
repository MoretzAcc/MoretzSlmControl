# Experimental console placement

Branch: `experiment/console-in-pattern`, based on `fork-windows` at `f3afce5`.
The experiment has been integrated into `fork-windows` at the user's request.

The console fits under the shorter Correction/Hologram controls. Its rectangle is
derived from their actual bottom edges, the boundary before Zernike, and the
pattern frame's existing bottom edge. Its size hints do not participate in the
pattern grid or the parent window layout. Long log text therefore scrolls inside
the available rectangle rather than widening the columns or increasing height.

The pattern frame has an inset lower-left corner: its outline passes above the
console and down its right edge. Console uses a regular section caption; Reset
session is in the top action row immediately before Export configuration.

Verification:

- 67 unittest tests ran successfully, with Unix signal delivery skipped on Windows.
- New geometry tests verify no overlap, resize/scaling adaptation and unchanged
  window/column dimensions with very long log entries and console captions.
- Native Windows checks also verify that sidebar dragging still works and that
  UI changes preserve SLM buffer dimensions and output bytes.
- Evidence: [pattern section](results/embedded-console.png),
  [whole window](results/embedded-console-window.png),
  [native measurements](results/embedded-console.json).

Native Linux rendering and other desktop themes have not been checked in this
experiment. The previous layout remains available at commit `f3afce5`.
