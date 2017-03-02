#!/usr/bin/python
# -*- coding: utf-8

import httplib, urllib,time,json,os,sys
import subprocess
PIPE = subprocess.PIPE

def startservice(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)

class IceClient:

    def __init__(self,server_ip,server_port,user,password):
        self.server_ip=server_ip
        self.server_port=server_port
        self.user=user
        self.password=password

    def connect(self):
        try:
            print "connect %s:%d" % (self.server_ip,self.server_port)
            self.conn = httplib.HTTPConnection("%s:%d" % (self.server_ip,self.server_port))
            print self.conn
            return True
        except:
            print "not connect"
            return False

    def _get(self,page,params=""):
        self.data=""
        if params!="":
            params="&"+params
        if not self.connect():
            print "error connect"
            return False
        try:
            self.conn.request("GET",page+"?_user=%s&_password=%s%s" % (self.user,self.password,params))
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

    def _download_price(self):
        self.dwprice=False
        if not self._get("/iceserv/myprice"):
            return False
        if self.data!="0":
            self.dwprice=True
        return True

    def _egais_get_mydocs(self):
        self.docs=0
        if not self._get("/egais/get/mydocs","status=1"):
            return False
        self.docs=json.loads(self.data)
        self.docs=len(self.docs)
        return True

    def _egais_get(self):
        if not self._get("/egais/get/docs"):
            return False
        return True

    def _egais_send(self):
        if not self._get("/egais/send/docs"):
            return False
        return True

    def _update_sets(self):
        if not self._get("/iceserv/regs_sets"):
            return False
        return True

    def _update_actions(self):
        if not self._get("/iceserv/actions"):
            return False
        return True

    def _upload_checks(self):
        if not self._get("/iceserv/trsc/send"):
            return False
        return True

    def _upload_zet(self):
        self.zet=False
        if not self._get("/iceserv/Zet/send"):
            return False
        if self.data!="0":
            self.zet=True
        return True

    def _upgrade_prog(self):
        self.upg=False
        if not self._get("/iceserv/upgrade/prog"):
            return False
        if self.data=="1":
            self.upg=True
        return True

    def _upgrade_base(self):
        self.upd=False
        if not self._get("/iceserv/upgrade/base"):
            return False
        if self.data=="1":
            self.upd=True
        return True

    def _restart_egais(self):
        if not self._get("/egais"):
            return False
        if self.data.find("egais_disconnected")!=-1:
            self.egais=False
        else:
            self.egais=True
        return True

    def _do_upgrade_base(self):
        l=os.listdir("/opt/IceCash/upgrades")
        l.sort()
        for s in l:
            print "Upgrade:",s
            os.system("rm -R /opt/IceCash/execute/*")
            res=os.system("cd /opt/IceCash/execute && tar -xpjf /opt/IceCash/upgrades/%s" % s)
            if res==0:
                res=os.system("cd /opt/IceCash/execute && sh install.sh")
                print "run upgrade",res
            else:
                print "error uppack bzip"
                res=2
            os.system("rm -R /opt/IceCash/execute/*")
            if res==0:
                os.system("rm /opt/IceCash/upgrades/%s" % s)
            else:
                sys.exit(res)
        print "upgrade complette"
        sys.exit(0)

if not len(sys.argv):
    sys.halt(1)

cmd=sys.argv[1]
ic = IceClient("localhost",10110,"kassir","766766")

if cmd=="dw_checks":
    ic._upload_checks()

if cmd=="dw_price":
    if ic._download_price():
        if ic.dwprice:
            startservice("gmessage -center -ontop -borderless -sticky -title 'ПРАЙС' -fg green -display :0 'Внимание, подгружен новый прайс.'")

if cmd=="dw_actions":
    ic._update_actions()

if cmd=="dw_sets":
    ic._update_sets()

if cmd=="dw_zets":
    if ic._upload_zet():
        if ic.zet:
            startservice("gmessage -center -ontop -borderless -sticky -title 'Z-Отчет' -fg blue -display :0 'Z-отчет успешно выгружен на сервер.'")

if cmd=="dw_upgrade_prog":
    if ic._upgrade_prog():
        if ic.upg:
            os.system("systemctl restart DTPrint")
            os.system("systemctl restart dIceCash")
            os.system("sh /home/kassir/dIceCash/upgrade.sh")
            startservice("gmessage -center -ontop -borderless -sticky -title 'Обновление' -fg red -display :0 'Внимание! произошло обновление программы. Сервис перезапущен и может не работать несколько секунд.\nВыйдите из режима регистрации спустя минутуу и вернитесь обратно. Интерфейс может поменятся.'")

if cmd=="dw_upgrade_base":
    if ic._upgrade_base():
        if ic.upd:
            ic._do_upgrade_base()

if cmd=="do_upgrade_base":
    ic._do_upgrade_base()

if cmd=="ex_egais":
    print ic._egais_get()
    print ic._egais_send()

if cmd=="vf_egais":
    ic._egais_get_mydocs()
    if ic.docs>0:
        startservice("gmessage -center -ontop -borderless -sticky -title 'ЕГАИС' -fg red -display :0 'Приняты новые документы ЕГАИС\nДокументы, в количестве - %s ожидают подтверждения'" % ic.docs)

if cmd=="restart_egais":
    if ic._restart_egais():
        if not ic.egais:
            print "error connect egais"
            os.system("service updater restart && sleep 5 && service utm restart")

#if cmd=="start_upload":
#    startservice("gmessage -center -ontop -borderless -sticky -title 'ПРАЙС' -fg green -display :0 'Запущена автоматическая выгрузка чеков'")
#    while True:
#        ic._upload_checks()
#        time.sleep(30)
#        ic._update_sets()
#        time.sleep(30)

