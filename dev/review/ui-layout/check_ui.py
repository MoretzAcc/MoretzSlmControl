import json,os,sys
from pathlib import Path
import numpy as np
from PySide6.QtCore import QTimer,QRect
from PySide6.QtWidgets import QApplication,QLineEdit
if sys.platform=='win32':
 from moretzslmcontrol.monitor_stuff.platform.windows import WindowsPlatformAdapter
 WindowsPlatformAdapter.get_screen_edids=lambda self,screen: []
from moretzslmcontrol.monitor_stuff.platform import create_platform_adapter
from moretzslmcontrol.monitor_stuff.monitor_manager import MonitorManager
from moretzslmcontrol.userinterface.main_window import MainWindow
app=QApplication([])
m=MonitorManager(app,create_platform_adapter(app.platformName()))
w=MainWindow(m);w.show()
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=True)
def capture():
 base=w._ui_scale; font=w._zernike_parameter_fields['defocus'].font().pointSizeF()
 w._change_ui_scale(.05);app.processEvents();w._change_ui_scale(-.05);app.processEvents()
 restored=w._zernike_parameter_fields['defocus'].font().pointSizeF()
 sizes={k:[v.width(),v.height()] for k,v in w._preview_labels.items()}
 controls=[*w.findChildren(QLineEdit),w._scale_up_button,w._scale_down_button,w._console]
 clipped=[{'name':v.toolTip() or v.metaObject().className(),'rect':[v.mapTo(w,v.rect().topLeft()).x(),v.mapTo(w,v.rect().topLeft()).y(),v.width(),v.height()]} for v in controls if v.isVisible() and not w.rect().contains(QRect(v.mapTo(w,v.rect().topLeft()),v.size()))]
 pattern=np.tile(np.linspace(0,2*np.pi,256,dtype=np.float32),(128,1))
 for label in w._preview_labels.values():w._set_preview_image(label,pattern)
 app.processEvents();w.grab().save(str(out/'ui.png'))
 r={'platform':app.platformName(),'screen':[app.primaryScreen().size().width(),app.primaryScreen().size().height()],'scale':base,'font_before':font,'font_restored':restored,'preview_sizes':sizes,'clipped':clipped,'zernike_order':list(w._zernike_parameter_fields)}
 (out/'result.json').write_text(json.dumps(r,indent=2));print(json.dumps(r),flush=True);os._exit(0)
QTimer.singleShot(2000,capture)
app.exec()
