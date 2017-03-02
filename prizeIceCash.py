#!/usr/bin/python
# -*- coding: utf8 -*-
# IcePrize client v 0.001
import string
import skserv
import sys
import time
import os

const_error=1
const_error_connect=2
const_error_wait=3

text_separator=";;"
msg_err="err"

class SkClient(skserv.SockClient):
    def run(self):
        accept=self.mrecv()
        if accept==skserv.msg_err:
            return 0
        lines = sys.stdin.readlines()
        error=0
        for line in lines:
            self.msend(line);
            error=self.mrecv()
            print error
            if str(error)==skserv.msg_err:
                break
        return 1

class prizeIceCash:
    def __init__(self,idsystem,idplace,nkassa,addr,port):
        self.addr=addr
        self.port=port
        self.idsystem=idsystem
        self.idplace=idplace
        self.nkassa=nkassa

    def connect(self):
        try:
            self.sc=SkClient(self.addr,self.port)
            self.data=self.sc.mrecv()
            #print "connect prize %s %s" % (self.addr,self.port)
            if self.data=='ok':
                return True
            else:
                return False
        except:
            self.sc=None
            print "error connect"
            return False

    def close(self):
        if self.sc!=None:
            self.sc.close()

    def cmd(self,_cmd,_params=[]):
        if self.sc==None:
            return False
        msg=skserv.separator.join([_cmd]+_params)
        #print msg
        self.sc.msend(msg)
        self.data=self.sc.mrecv()
        if len(self.data)==0:
            return False
        else:
            if self.data==msg_err:
                return False
            return True

    def cmd_info(self):
        result = self.cmd("info",[self.idsystem])
        if result:
            self.info=self.data.replace(text_separator," ").decode("utf8")
        else:
            self.info=""
        return result

    def cmd_gen(self,ncheck,idtrsc,summa):
        result=self.cmd("gen",[str(self.idsystem),str(self.idplace),str(self.nkassa),str(ncheck),str(idtrsc),str(summa)])
        if result:
            keys=["idtrsc","idprize","type","idtov"]
            self.gen=dict(zip(keys,self.data.split(skserv.separator)))
            self.gen['idtov']=self.gen['idtov'].decode('utf8')
        else:
            self.gen={}
        print self.gen
        return result

    def cmd_close(self,idtrsc=None):
        if idtrsc==None:
            idtrsc=self.gen['idtrsc']
        result = self.cmd("close",[str(self.idsystem),str(idtrsc)])
        if result:
            pass
            #print self.data
        else:
            pass
        return result

