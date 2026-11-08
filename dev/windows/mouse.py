#!/usr/bin/env python3
"""Move the virtual USB tablet; give Windows time to observe button transitions."""
import json
import subprocess
import sys
import time
x, y = map(int, sys.argv[1:3])
def send(events):
    subprocess.run(['python3', '/home/rolf/projects/windows-test-lab/vm.py', 'qmp', json.dumps({'execute': 'input-send-event', 'arguments': {'events': events}})], check=True)
send([{'type': 'abs', 'data': {'axis': 'x', 'value': round(x / 1279 * 32767)}}, {'type': 'abs', 'data': {'axis': 'y', 'value': round(y / 799 * 32767)}}])
if '--click' in sys.argv:
    time.sleep(.1)
    send([{'type': 'btn', 'data': {'button': 'left', 'down': True}}])
    time.sleep(.1)
    send([{'type': 'btn', 'data': {'button': 'left', 'down': False}}])
