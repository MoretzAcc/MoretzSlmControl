#!/usr/bin/env python3
"""Repeat a genuine Explorer thumbnail Peek test; reject inactive reference trials."""
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
import argparse,json,subprocess,time,sys
ROOT=Path('/home/rolf/.local/share/windows-test');HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('--reuse',action='store_true');p.add_argument('--taskbar-x',type=int,default=None);p.add_argument('--thumbnail-x',type=int,default=None);args=p.parse_args()
ready=ROOT/'results/interactive-ready.json'
def run(*words):subprocess.run(words,check=True,stdout=subprocess.DEVNULL)
def mouse(x,y):run(sys.executable,str(HERE/'mouse.py'),str(x),str(y))
def screenshot(name):
 target=ROOT/'results'/name
 run(sys.executable,str(HERE/'vm.py'),'screenshot',str(target));return Image.open(target).convert('RGB')
if not args.reuse:
 stamp=ready.stat().st_mtime_ns if ready.exists() else 0
 run(sys.executable,str(HERE/'vm.py'),'job',str(HERE/'run-peek-interactive.ps1'))
 end=time.monotonic()+60
 while not ready.exists() or ready.stat().st_mtime_ns<=stamp:
  if time.monotonic()>end:raise SystemExit('Guest probe did not become ready')
  time.sleep(.1)
r=json.loads(ready.read_text())
r['test']='Two repeated native Explorer taskbar-thumbnail hover trials with USB tablet input'
r['trials']=[]
if args.taskbar_x is None:
 image=screenshot('taskbar-ready.png')
 if image.size != (1280,800):raise SystemExit('This VM test expects a 1280x800 console')
 template=Image.open(HERE/'taskbar-control-icon.png').convert('RGB')
 candidates=[]
 for x in range(8,1272):
  score=sum(ImageStat.Stat(ImageChops.difference(template,image.crop((x-8,767,x+8,783)))).mean)/3
  candidates.append((score,x))
 score,args.taskbar_x=min(candidates)
 if score>12:raise SystemExit('Taskbar icon not found; inspect screenshot or pass --taskbar-x')
if args.thumbnail_x is None:args.thumbnail_x=args.taskbar_x
r['taskbar_icon_x']=args.taskbar_x
for index in range(2):
 mouse(1160,80);time.sleep(1)
 before=screenshot(f'taskbar-{index+1}-before.png')
 mouse(args.taskbar_x,775);time.sleep(1)
 screenshot(f'taskbar-{index+1}-thumbnail.png')
 mouse(args.thumbnail_x,716);time.sleep(1.5)
 active=screenshot(f'taskbar-{index+1}-active.png')
 mouse(1160,80);time.sleep(1)
 restored=screenshot(f'taskbar-{index+1}-restored.png')
 def differences(image):
  result=[]
  for x,y,w,h in r['window_geometry']:
   box=(x+30,y+30,x+w-30,y+h-30)
   result.append(sum(ImageStat.Stat(ImageChops.difference(before.crop(box),image.crop(box))).mean)/3)
  return result
 d=differences(active);restore=differences(restored)
 r['trials'].append({'active_difference':d,'restored_difference':restore})
 r['checks'] += [{'name':f'trial {index+1}: unprotected reference changes under Peek','pass':d[0]>15},
                 {'name':f'trial {index+1}: protected output stays pixel-identical','pass':d[1]==0},
                 {'name':f'trial {index+1}: both outputs restore after leaving the thumbnail','pass':max(restore)<2}]
 print('Trial',index+1,'active differences',d,'restored',restore,flush=True)
(ROOT/'results/taskbar-repeated-result.json').write_text(json.dumps(r,indent=2))
# Close only this test's control window; its close event releases native resources.
run(sys.executable,str(HERE/'mouse.py'),'80','60','--click')
time.sleep(.5)
run(sys.executable,str(HERE/'vm.py'),'qmp',json.dumps({'execute':'send-key','arguments':{'keys':[{'type':'qcode','data':'alt'},{'type':'qcode','data':'f4'}],'hold-time':100}}))
if not all(c['pass'] for c in r['checks']):raise SystemExit('A reference, protected output or restoration expectation failed')
print('All',len(r['checks']),'native taskbar expectations passed.')
