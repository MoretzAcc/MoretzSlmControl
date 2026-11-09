"""Launch the real Windows GUI in VMs whose WMI monitor provider is unavailable."""
from moretzslmcontrol.monitor_stuff.platform.windows import WindowsPlatformAdapter

WindowsPlatformAdapter.get_screen_edids = lambda self, screen: []

from moretzslmcontrol.app import main

main()
