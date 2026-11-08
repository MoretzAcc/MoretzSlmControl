"""Native Windows A/B proof: production DisplayWindow with/without DWM Peek protection."""
from __future__ import annotations
import ctypes,json,os,platform,sys,traceback,urllib.request
from pathlib import Path
import numpy as np
from PIL import ImageGrab
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication,QLabel
from moretzslmcontrol.hologram_manager import HologramManager
from moretzslmcontrol.monitor_stuff.platform.windows import WindowsPlatformAdapter
import moretzslmcontrol.monitor_stuff.platform.windows as windows_platform
from moretzslmcontrol.userinterface.display_bridge import DisplayBridge
from moretzslmcontrol.userinterface.display_window import DisplayWindow
from heros import zenoh

ROOT=Path('C:/Lab/peek');ROOT.mkdir(exist_ok=True)
app=QApplication([])
app.setQuitOnLastWindowClosed(False)
class ControlWindow(QLabel):
 def closeEvent(self,event):
  finish();event.accept()
control=ControlWindow('Windows native Aero Peek test: left baseline, right protected')
control.setWindowTitle('Aero Peek control');control.setGeometry(40,30,1000,60);control.show()
adapter=WindowsPlatformAdapter();screen=app.primaryScreen()
setter=ctypes.WinDLL('dwmapi').DwmSetWindowAttribute
setter.argtypes=(ctypes.c_void_p,ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32);setter.restype=ctypes.c_int32
getter=ctypes.WinDLL('dwmapi').DwmGetWindowAttribute
getter.argtypes=setter.argtypes;getter.restype=ctypes.c_int32
user=ctypes.WinDLL('user32')
windows=[];managers=[]
actual_exclusion=windows_platform.exclude_from_peek
native_exclusion_results=[]
def observe_exclusion(hwnd):
    result=actual_exclusion(hwnd)
    native_exclusion_results.append({'hwnd':hwnd,'success':result})
    return result
windows_platform.exclude_from_peek=observe_exclusion
report={'windows_version':platform.platform(),'python':sys.version,'qt_platform':app.platformName(),'checks':[]}
composition=ctypes.c_int32()
composition_hr=ctypes.WinDLL('dwmapi').DwmIsCompositionEnabled(ctypes.byref(composition))
report['dwm_composition']={'hresult':composition_hr,'enabled':bool(composition.value)}
def upload(name,data):
 token=os.environ['WINDOWS_TEST_BRIDGE_TOKEN']
 request=urllib.request.Request('http://10.0.2.2:8765/'+name,data=data,headers={'Authorization':'Bearer '+token},method='POST')
 urllib.request.urlopen(request,timeout=20).read()
def check(name,ok,**extra):report['checks'].append({'name':name,'pass':bool(ok),**extra})
def attrs(window):
 out={}
 for attribute in (11,12):
  value=ctypes.c_int32()
  result=getter(ctypes.c_void_p(int(window.winId())),attribute,ctypes.byref(value),4)
  out[str(attribute)]={'hresult':result,'value':value.value if result==0 else None}
 return out
for index in range(2):
 bridge=DisplayBridge(f'peek-{index}')
 manager=HologramManager(320,480,f'peek-{index}',f'Peek {index}',bridge,lambda _:None,heros_enabled=False)
 manager.setHologramPattern(np.broadcast_to(np.linspace(-np.pi,np.pi,480,endpoint=False,dtype=np.float32),(320,480)).copy())
 window=DisplayWindow(f'peek-{index}',f'Peek {index}',manager,adapter)
 window.attach_to_screen(screen)
 window.showNormal();window.setGeometry(40+index*560,180,480,320);window.show()
 window.refresh_from_displayer(force=True)
 windows.append(window);managers.append(manager)
value=ctypes.c_int32(0)
check('baseline protection explicitly disabled',all(setter(ctypes.c_void_p(int(windows[0].winId())),attr,ctypes.byref(value),4)==0 for attr in (11,12)))
report['adapter_exclusion_calls']=native_exclusion_results
check('production adapter applies native exclusion to both outputs',len(native_exclusion_results)==2 and all(r['success'] for r in native_exclusion_results))
check('protected HWND remains identical after side-by-side layout',native_exclusion_results[1]['hwnd']==int(windows[1].winId()))
report['attributes_before']=[attrs(w) for w in windows]
report['window_geometry']=[w.geometry().getRect() for w in windows]
report['device_pixel_ratio']=screen.devicePixelRatio()
check('DWM composition is enabled',composition_hr==0 and composition.value!=0)
control.activateWindow();control.raise_()
before=None

def capture_before():
 global before
 try:
  before=ImageGrab.grab(all_screens=True).convert('RGB')
  before.save(ROOT/'before.png');upload('peek-before.png',(ROOT/'before.png').read_bytes())
  if not os.environ.get('WINDOWS_PEEK_EXTERNAL_INPUT'):
   user.keybd_event(0x5B,0,1,0);user.keybd_event(0xBC,0,0,0)
  QTimer.singleShot(2000,capture_peek)
 except Exception:
  report['exception']=traceback.format_exc();finish()
def capture_peek():
 try:
  peek=ImageGrab.grab(all_screens=True).convert('RGB')
  peek.save(ROOT/'peek.png');upload('peek-active.png',(ROOT/'peek.png').read_bytes())
  differences=[]
  for window in windows:
   g=window.geometry();dpr=screen.devicePixelRatio();box=tuple(round(v*dpr) for v in (g.x()+30,g.y()+30,g.x()+g.width()-30,g.y()+g.height()-30))
   a=np.array(before.crop(box)).astype(np.int16);b=np.array(peek.crop(box)).astype(np.int16)
   differences.append(float(np.abs(a-b).mean()))
  report['pixel_mean_absolute_difference']=differences
  check('Peek demonstrably affects unprotected reference',differences[0]>15,difference=differences[0])
  check('protected output remains visually unchanged during Peek',differences[1]<2,difference=differences[1])
  report['attributes_after']=[attrs(w) for w in windows]
 except Exception:report['exception']=traceback.format_exc()
 finally:
  user.keybd_event(0xBC,0,2,0);user.keybd_event(0x5B,0,2,0)
  user.keybd_event(0x1B,0,0,0);user.keybd_event(0x1B,0,2,0)
  QTimer.singleShot(1500,finish)
def finish():
 try:
  ImageGrab.grab(all_screens=True).save(ROOT/'restored.png');upload('peek-restored.png',(ROOT/'restored.png').read_bytes())
  (ROOT/'result.json').write_text(json.dumps(report,indent=2));upload('peek-result.json',(ROOT/'result.json').read_bytes())
 finally:
  for manager in managers:manager.close()
  app.quit()
def normalize_input():
 user.keybd_event(0xBC,0,2,0);user.keybd_event(0x5B,0,3,0)
 user.SetCursorPos(80,60);user.mouse_event(2,0,0,0,0);user.mouse_event(4,0,0,0,0)
 QTimer.singleShot(1000,capture_before)
if '--interactive' in sys.argv:
 def ready():
  ImageGrab.grab(all_screens=True).save(ROOT/'before.png')
  upload('interactive-before.png',(ROOT/'before.png').read_bytes())
  upload('interactive-ready.json',json.dumps(report).encode())
 QTimer.singleShot(1500,ready)
 QTimer.singleShot(180000,finish)
else:
 QTimer.singleShot(1000,normalize_input)
app.exec()
# Isolated GUI probe: Windows releases handles at process exit. Avoid Zenoh global teardown blocking the job agent.
os._exit(0)
