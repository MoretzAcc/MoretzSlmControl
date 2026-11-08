# Virtual monitor review lab

This lab tests the unmodified production application on real Qt `QScreen` objects supplied by an isolated Xorg dummy server. It does not mock monitor discovery, invent successful EDID detection, or change the user's KDE monitor configuration.

## Prerequisites (Debian 13)

```sh
sudo apt-get install xserver-xorg-video-dummy openbox x11-xserver-utils
uv sync --locked
```

Start the isolated server in a dedicated terminal, from the repository root:

```sh
sudo Xorg :99 -config "$PWD/dev/review/xorg-dummy.conf" \
  -logfile /tmp/moretz-review-Xorg.log -noreset -nolisten tcp \
  -ac -novtswitch -sharevts
```

In another terminal:

```sh
DISPLAY=:99 openbox
```

`-ac` permits local connections to this disposable display; TCP listening is disabled. Stop the isolated server and Openbox after testing. The original review run was cleaned up; restart both before rerunning the matrix. Do not apply this configuration to the normal display server. Check `:99` is unused before starting.

Run the matrix from a third terminal:

```sh
UV="$HOME/.local/bin/uv" bash dev/review/run_matrix.sh
```

Current runs write to `dev/review/fork-results/` (`REVIEW_RESULTS_DIR` overrides it); the historical baseline under `results/` is preserved. The runner fails on a product expectation failure or exception.

The runner defaults to display `:99` (`REVIEW_DISPLAY` overrides it), sets XCB, and clears inherited Xauthority/Wayland settings. Xorg uses 512 MiB of configured video memory because an 8192 x 8192 virtual framebuffer at 32 bpp exceeds 256000 KiB. The dummy driver has a 300 MHz pixel-clock limit: the 4K mode uses about 30 Hz, not 60 Hz.

## Monitor examples

```sh
export DISPLAY=:99
# Portrait output to the right of the main screen:
xrandr --addmode DUMMY1 1080x1920
xrandr --output DUMMY0 --mode 1920x1080 --pos 0x0 --primary \
       --output DUMMY1 --mode 1080x1920 --pos 1920x0
# Disconnect/reconnect without restarting the application:
xrandr --output DUMMY1 --off
xrandr --output DUMMY1 --mode 1080x1920 --pos 1920x0
# Change the main output's geometry:
xrandr --output DUMMY0 --mode 1280x800
xrandr --listmonitors
```

Other matrix modes are 1024x768, 1280x800, 1920x1080, 1080x1920, 3440x1440, and 3840x2160. The three-screen layout has offsets 0, 1920 and 3000 pixels. Extra modes are installed with `xrandr --newmode` and `--addmode`; see the runner for exact timings. Restore the lab with:

```sh
DISPLAY=:99 xrandr --output DUMMY1 --off --output DUMMY2 --off \
  --output DUMMY0 --mode 1920x1080 --pos 0x0
```

To use the application manually inside the lab, start `DISPLAY=:99 uv run moretzslmcontrol`; attach an X11 viewer or use `DISPLAY=:99 scrot capture.png` for the isolated desktop. The test harness also saves widget and desktop screenshots directly.

## Evidence and interpretation

`exercise_ui.py` creates the actual `MainWindow`, `LinuxPlatformAdapter`, `MonitorManager`, output windows and HERO resources. QtTest sends keyboard/mouse events to controls. File dialogs are replaced only with deterministic paths to generated NPY/BMP fixtures and a temporary configuration file. Numerical comparisons allow one circular gray-level difference due to float32 phase wrapping/rounding. File fixtures are removed after each process.

The full-HD scenario injects `time.sleep(5)` into the real Zernike and modification calculation callables. Actual calculations still run after the delay. It measures typing latency, queued work, eventual values and the return-to-previous-value race. This models the requested five-second calculation rather than claiming all real hardware takes five seconds.

JSON files contain individual expectations, observed values and failures. The harness collects evidence even after a failed expectation; the current matrix runner checks every expected scenario and exits unsuccessfully if any expectation or exception is recorded. The historical baseline predates this strict aggregate check. Logs and screenshots accompany the JSON. `*-ui.png` captures the whole widget (which may exceed the monitor); `*-desktop.png` shows actual clipping on the monitor. `*-output.png` captures the native SLM window.

### Limitations

- Dummy Xorg outputs do not create DRM EDIDs in `/sys/class/drm`. The upstream baseline merged distinct screens; F01 fixed the production fallback. Current tests use that actual fallback without a shim and verify three independent sessions, secondary-only disconnect and reconnect.
- The harness imports the production UI and platform components directly to instrument them; it does not execute `app.main()` during each scenario. A normal application launch was separately verified in KDE.
- Isolated screenshots use the default Qt/X11 theme, not the user's KDE dark palette. The fixed-size layout issues are visible in both environments.
- DPI is 1.0 in this matrix. Fractional scaling, physical EDID/bit depth, Windows/Aero Peek, optical SLM behavior and physical refresh timing are not verified.
- The baseline review describes the old upstream behavior. See FORK-VALIDATION.md for actual fork results; Windows/physical/scaling limits remain.

See [REVIEW.md](REVIEW.md) for findings and prioritized improvements, and [results/](results/) for evidence.
