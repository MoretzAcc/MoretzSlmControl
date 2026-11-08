#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
export DISPLAY=${REVIEW_DISPLAY:-:99}
unset WAYLAND_DISPLAY XAUTHORITY
export QT_QPA_PLATFORM=xcb
UV=${UV:-/home/rolf/.local/bin/uv}
mkdir -p dev/review/results
xrandr --newmode review-ultrawide 265.25 3440 3488 3520 3600 1440 1443 1453 1474 +HSync -VSync 2>/dev/null || true
xrandr --newmode review-4k 266.625 3840 3888 3920 4000 2160 2163 2168 2222 +HSync -VSync 2>/dev/null || true
xrandr --addmode DUMMY0 review-ultrawide
xrandr --addmode DUMMY0 review-4k
xrandr --addmode DUMMY1 1080x1920
xrandr --addmode DUMMY2 review-4k
xrandr --output DUMMY0 --mode 1920x1080 --pos 0x0 --primary --output DUMMY1 --mode 1080x1920 --pos 1920x0 --output DUMMY2 --mode review-4k --pos 3000x0
"$UV" run --locked python dev/review/exercise_ui.py --name three-monitors --collision-only > dev/review/results/three-monitors.log 2>&1
xrandr --output DUMMY1 --off --output DUMMY2 --off
for item in 'small:1024x768' 'vm:1280x800' 'portrait:1080x1920' 'ultrawide:review-ultrawide' '4k:review-4k'; do
    name=${item%%:*}
    mode=${item#*:}
    xrandr --output DUMMY0 --mode "$mode" --pos 0x0
    "$UV" run --locked python dev/review/exercise_ui.py --name "$name" > "dev/review/results/$name.log" 2>&1
    echo "Completed $name"
done
xrandr --output DUMMY0 --mode 1920x1080 --pos 0x0
"$UV" run --locked python dev/review/exercise_ui.py --name full-hd-slow-hotplug --slow --hotplug > dev/review/results/full-hd-slow-hotplug.log 2>&1
xrandr --output DUMMY1 --off --output DUMMY2 --off --output DUMMY0 --mode 1920x1080 --pos 0x0
"$UV" run --locked python -m unittest discover -s tests > dev/review/results/unittest.log 2>&1
"$UV" run --locked ruff check . > dev/review/results/ruff.log 2>&1 || true
