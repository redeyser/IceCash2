#!/usr/bin/python
# -*- coding: utf-8
import httplib, urllib,urllib2
from poster.encode import multipart_encode
from poster.streaminghttp import register_openers
import subprocess
import xml.etree.ElementTree as etree
import sys,os
PIPE = subprocess.PIPE

def _dialog_menu(title,menu):
    cmd = "dialog --clear --stdout --title \"%s\" --menu \"Сделайте выбор:\" 20 50 10 %s" % (title,menu)
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    data=p.stdout.read()
    while p.poll()==None:
        pass
    result=int(p.returncode)
    return result,data

def _dialog_file(title,home):
    cmd = "dialog --clear --stdout --title \"%s\" --fselect %s 10 50" % (title,home)
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
    data=p.stdout.read()
    while p.poll()==None:
        pass
    result=int(p.returncode)
    return result,data

def _dialog_msg(title,text):
    cmd = "dialog --clear --title \"%s\" --msgbox \"%s\" 10 50" % (title,text)
    os.system(cmd)
    return 0


class IceServClient:

    def __init__(self,server,port,user,password):
        self.server_port=int(port)
        self.server_ip=server
        self.regid=user
        self.password=password
        self.path="/"
        self.dirs=[]

    def connect(self):
        try:
            self.conn = httplib.HTTPConnection("%s:%d" % (self.server_ip,self.server_port))
            return True
        except:
            print "not connect"
            return False


    def get_file(self,page,fn):
        return urllib.urlretrieve(page, fn)

    def put_file(self,path,fname):
        register_openers()
        #print path,fname
        data, headers = multipart_encode({"file": open(fname, "rb"),'_user': self.regid,'_password':self.password})
        request = urllib2.Request("http://%s:%d/files/%s" % (self.server_ip,self.server_port,path), data, headers)
        try:
            result = urllib2.urlopen(request)
            if result.code==200:
                result=0
            else:
                result=1
        except:
            result=1
        return result

    def get(self,_type,page,params):
        self.data=""
        if not self.connect():
            print "error connect"
            return False
        params.update({"_user":self.regid,"_password":self.password})
        if _type=='GET':
            p=''
            for k,v in params.items():
                if p!='':
                    p+='&'
                p+="%s=%s" %(k,v)
            page=page+"?"+p
        params=urllib.urlencode(params)
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/xml"}
        #print page,params
        try:
            self.conn.request(_type,page,params,headers)
            response = self.conn.getresponse()
            if response.status!=200:
                print "error_status"
                return False
            self.data=response.read()
        except:
            print "error get data"
            return False
        finally:
            self.conn.close()
        return True


    def _getdir(self,path):
        cmd=""
        if self.get('GET','/fo/ls',{"path":path}):
            xml=etree.fromstring(self.data)
            dirs=["/"]
            files=[]
            if (xml.tag=='data'):
                #print self.data
                b=xml.find("body")
                for line in b:
                    if line.tag=='file':
                        files.append(path+"/"+line.text)
                    if line.tag=='dir':
                        dirs.append(path+"/"+line.text)
                    if line.tag=='cur':
                        cur=line.text
                self.path=path
                self.dirs=dirs
                self.files=files
                #print "CUR=",cur
                #print "DIRS=",dirs
            d=""
            for v in dirs:
                d+="\"%s\" \"dir\" " % (v)
            for v in files:
                d+="\"%s\" \"file\" " % (v)
            cmd = "dialog --clear --title --stdout \"Выберите файл для скачивания\" --menu \"Скачать из:\" 20 51 20 %s" % (d)
        return cmd

    def _selectfile(self,path):
        self.path=path
        result=0
        isfile=False
        while not isfile and result==0:
            cmd=self._getdir(self.path)
            p = subprocess.Popen(cmd, shell=True, stdout=PIPE)
            data=p.stdout.read()
            while p.poll()==None:
                pass
            result=int(p.returncode)
            if data in self.files:
                isfile=True
                self.path=data
            if data in self.dirs:
                isfile=False
                self.path=data
        return result
            
        
    def download_file(self,_dir=""):
        if self.get('GET','/files%s' % (self.path),{}):
            try:
                if _dir!="" and _dir[-1]!="/":
                    _dir+="/"
                f=open(_dir+os.path.basename(self.path),"wb")
                f.write(self.data)
                f.close()
            except:
                return False
            return True
        else:
            return False
        
print "IceServ transport 1.0.01"
if len(sys.argv)<6 and len(sys.argv)>1:
    print "help:"
    print "\t./_is_transport.py <regname> <password> <operation> <filename> <dirname>"
    print "\tregname\t\t Можно указать def"
    print "\tpassword\t Можно указать def"
    print "\toperation\t (upload,download)"
    print "\tfilename\t В случае upload - путь до локального файла, в случае download - путь до файла на сервере."
    print "\tdirname\t\t В случае upload - путь к папке на сервере, в случае download - путь к локальной папке."
    print "Пример скачивания: ./_is_transport.py def def download /upload/.vimrc /root"
    print "Пример отравки: ./_is_transport.py def def upload /home/user/.icewm/startup /upload"
    sys.exit(0)
if len(sys.argv)==6:
    (pname,_regid,_pswd,_oper,_file,_dir) = sys.argv
    packet=True
    if _regid=='def':
        _regid="beerkem"
    if _pswd=='def':
        _pswd="644644"
    r=0
else:
    packet=False
    _regid="beerkem"
    _pswd="644644"
    _dir=""

ic=IceServClient("IceServ",10100,_regid,_pswd)
if not ic.connect():
    sys.exit(1)

if not packet:
    r,_oper=_dialog_menu("Выбор операции","\"download\" \"Скачать\" \"upload\" \"Загрузить\"")

if int(r)!=0:
    sys.exit(1)

if _oper=='upload':
    if not packet:
        r,_file=_dialog_file("Выбор файла для загрузки","./")
    if r==0:
        if not packet:
            r,_dir=_dialog_menu("Куда загрузить?","\"\" \"/\" \"download\" \"dir\" \"upload\" \"dir\" \"script\" \"dir\" \"download/upgrade\" \"dir\" \"download/price\" \"dir\"")
        r=ic.put_file(_dir,_file)
        if r==0:
            if not packet:
                _dialog_msg("Результат","Файл %s отправлен на сервер в каталог %s" % (_file,_dir))
        else:
            if not packet:
                _dialog_msg("Результат","Ошибка отправки")
    print r
    sys.exit(r)


if _oper=='download':
    if not packet:
        r=ic._selectfile("")
    else:
        ic.path=_file
    if r==0:
        r=ic.download_file(_dir)
        if r:
            r=0
            if not packet:
                _dialog_msg("Результат","Файл %s скачан с сервера" % (ic.path))
        else:
            r=1
            if not packet:
                _dialog_msg("Результат","Ошибка скачивания")
    print r
    sys.exit(r)
sys.exit(1)
