#!/usr/bin/python
import clientDrv,sys,datetime

if len(sys.argv)<2:
    print "add parameters server port printer"
    sys.exit(1)
(server,port,printer)=sys.argv[1:4]
if len(sys.argv)>4:
    style=sys.argv[4]
else:
    style=""
if style.find("b")!=-1:
    bright=10
else:
    bright=0
if style.find("i")!=-1:
    invert=1
else:
    invert=0
if style.find("h")!=-1:
    height=1
else:
    height=0
if style.find("f")!=-1:
    font=3
else:
    font=0
if style.find("w")!=-1:
    big=1
else:
    big=0
if style.find("+")!=-1:
    head=True
else:
    head=False
if style.find("-")!=-1:
    cut=True
else:
    cut=False
if style.find("*")!=-1:
    beep=True
else:
    beep=False

drv = clientDrv.DTPclient(server,int(port),"dtpadm")
if not drv.connect():
    sys.exit(1)
text=sys.stdin.read()
text=text.replace("<BR>","\n")
text=text.replace("<","&lt")
text=text.replace(">","&gt")
if beep:
    drv._cm(printer,"_beep",{})
dt=datetime.datetime.today()
tm=dt.strftime("%Y-%m-%d %H:%M")
if head:
    drv._cm(printer,"prn_lines",{'text':tm,"width":0,"height":0,"font":0,"bright":10,"big":0,"invert":1,"align":"centers"})
r=drv._cm(printer,"prn_lines",{'text':text.decode("utf8"),"width":0,"height":height,"font":font,"bright":bright,"big":big,"invert":invert,"align":"left"})
if cut:
    drv._cm(printer,"_cut",{"type":0})
#r=drv._cm(printer,"prn_lines",{'text':u"\n\n\n\n\n\n\n","width":0,"height":1,"font":0,"bright":10,"big":0,"invert":0,"align":"left"})
print r
if r:
    sys.exit(0)
else:
    sys.exit(1)

