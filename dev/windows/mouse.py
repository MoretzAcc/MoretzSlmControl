#!/usr/bin/env python3
import subprocess,json,sys
x,y=map(int,sys.argv[1:3])
events=[{'type':'abs','data':{'axis':'x','value':round(x/1279*32767)}},{'type':'abs','data':{'axis':'y','value':round(y/799*32767)}}]
if '--click' in sys.argv:events+=[{'type':'btn','data':{'button':'left','down':True}},{'type':'btn','data':{'button':'left','down':False}}]
subprocess.run(['python3','/home/rolf/projects/windows-test-lab/vm.py','qmp',json.dumps({'execute':'input-send-event','arguments':{'events':events}})],check=True)
