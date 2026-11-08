#!/bin/bash
set -eu
cd "$(dirname "$0")/../.."
export DISPLAY=${REVIEW_DISPLAY:-:99}
unset WAYLAND_DISPLAY XAUTHORITY
export QT_QPA_PLATFORM=xcb
UV=${UV:-/home/rolf/.local/bin/uv}
RESULTS=${REVIEW_RESULTS_DIR:-dev/review/fork-results}
export REVIEW_RESULTS_DIR="$RESULTS"
mkdir -p "$RESULTS"
xrandr --newmode review-ultrawide 265.25 3440 3488 3520 3600 1440 1443 1453 1474 +HSync -VSync 2>/dev/null || true
xrandr --newmode review-4k 266.625 3840 3888 3920 4000 2160 2163 2168 2222 +HSync -VSync 2>/dev/null || true
xrandr --addmode DUMMY0 review-ultrawide
xrandr --addmode DUMMY0 review-4k
xrandr --addmode DUMMY1 1080x1920
xrandr --addmode DUMMY2 review-4k
xrandr --output DUMMY0 --mode 1920x1080 --pos 0x0 --primary --output DUMMY1 --mode 1080x1920 --pos 1920x0 --output DUMMY2 --mode review-4k --pos 3000x0
"$UV" run --locked python dev/review/exercise_ui.py --name three-monitors --collision-only --multi > "$RESULTS"/three-monitors.log 2>&1
xrandr --output DUMMY1 --off --output DUMMY2 --off
for item in 'small:1024x768' 'vm:1280x800' 'portrait:1080x1920' 'ultrawide:review-ultrawide' '4k:review-4k'; do
    name=${item%%:*}
    mode=${item#*:}
    xrandr --output DUMMY0 --mode "$mode" --pos 0x0
    "$UV" run --locked python dev/review/exercise_ui.py --name "$name" > "$RESULTS/$name.log" 2>&1
    echo "Completed $name"
done
xrandr --output DUMMY0 --mode 1920x1080 --pos 0x0
"$UV" run --locked python dev/review/exercise_ui.py --name full-hd-slow-hotplug --slow --hotplug > "$RESULTS"/full-hd-slow-hotplug.log 2>&1
xrandr --output DUMMY1 --off --output DUMMY2 --off --output DUMMY0 --mode 1920x1080 --pos 0x0
"$UV" run --locked python -m unittest discover -s tests > "$RESULTS"/unittest.log 2>&1
"$UV" run --locked ruff check . > "$RESULTS"/ruff.log 2>&1
python3 - "$RESULTS" <<'VERIFY'
import json, sys
from pathlib import Path
names = ('three-monitors', 'small', 'vm', 'portrait', 'ultrawide', '4k', 'full-hd-slow-hotplug')
failed = []
for name in names:
    data = json.loads((Path(sys.argv[1]) / f'{name}.json').read_text())
    failed.extend(f"{name}: {check['name']}" for check in data['checks'] if not check['pass'])
    if 'exception' in data:
        failed.append(f'{name}: unhandled exception')
if failed:
    raise SystemExit('\n'.join(failed))
print('All integration expectations passed.')
VERIFY
