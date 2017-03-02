import os;
import sys;
import re;
import subprocess
PIPE = subprocess.PIPE
def lsdir(dir):
    cmd='ls %s' % dir
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    files=p.stdout.read().split("\n")
    del files[len(files)-1]
    return files

def lsserial(f=""):
    cmd='ls /dev/ttyS*'
    if f!="":
        f=" | grep %s" % f
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    lsserial1=p.stdout.read().split("\n")
    del lsserial1[len(lsserial1)-1]
    cmd='ls /dev/serial/by-id/*'+f
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    lsserial2=p.stdout.read().split("\n")
    del lsserial2[len(lsserial2)-1]
    if f=="":
        return lsserial1+lsserial2
    else:
        return lsserial2

def lsusb():
    cmd='lsusb'
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    lsusb=p.stdout.read().split("\n")
    devices={}
    for l in lsusb:
        if l!='':
            r=re.search("ID (.+?) ",l)
            uid=r.group(1)
            if not devices.has_key(uid):
                p = subprocess.Popen("lsusb -vvv -d %s" % uid, shell=True, stdout=PIPE)
                lsv=p.stdout.read()
                r=re.search("idVendor *0x(.{4})",lsv)
                idvendor=r.group(1)
                r=re.search("idProduct *0x(.{4})",lsv)
                idproduct=r.group(1)
                r=re.search("iManufacturer *\d+ (.*?)\n",lsv)
                vendor=r.group(1)
                r=re.search("iProduct *\d+ (.*?)\n",lsv)
                product=r.group(1)
                epout=""
                epin=""
                interface=""
                r=re.search("iInterface *(\d*)",lsv)
                if r!=None:
                    interface=r.group(1)
                r=re.search("bEndpointAddress *(0x.*?) .*?OUT\n",lsv)
                if r!=None:
                    epout=r.group(1)
                r=re.search("bEndpointAddress *(0x.*?) .*?IN\n",lsv)
                if r!=None:
                    epin=r.group(1)
                devices[uid]=[idvendor,idproduct,vendor,product,interface,epin,epout]
    return devices
