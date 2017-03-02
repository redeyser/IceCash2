#!/usr/bin/python
# -*- coding: utf8 -*-
# IceBonus client v 0.001
import string
import skserv
import sys
import time
import os

const_error=1
const_error_connect=2
const_error_wait=3

CARD_DISCONT=2
CARD_CERT=1
CARD_BONUS=0

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

class bsIceCash:
    def __init__(self,place,nkassa,addr,port):
        self.addr=addr
        self.port=port
        self.place=place
        self.nkassa=nkassa
        self.sc=None

    def connect(self):
        try:
            self.sc=SkClient(self.addr,self.port)
            self.data=self.sc.mrecv()
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

    def cmd(self,_cmd,_card,_summa=0,_ncheck=0,_idtrsc=0):
        if self.sc==None:
            return False
        arr=[_cmd,_card,str(self.place),str(self.nkassa),str(_ncheck),str(_idtrsc),str(_summa)]
        msg=skserv.separator.join(arr)
        #print msg
        self.sc.msend(msg)
        self.data=self.sc.mrecv()
        if len(self.data)==0:
            return False
        else:
            return True

    def cmd_ping(self):
        return self.cmd("ping","0")

    def cmd_info(self,_card):
        self.info={}
        fd=['id','shk','name_f','name_i','name_o','type','discount','dtborn','off','sum','dedproc','addproc']
        result = self.cmd("info",_card)
        if result:
            data=self.data.split(skserv.separator)
            if len(data)<11:
                return False
            for i in range(12):
                self.info[fd[i]]=data[i]
        return True

    def cmd_addsum(self,_card,_sum,_ncheck,_idtrsc):
        return self.cmd("addsum",_card,_sum,_ncheck,_idtrsc)

    def cmd_dedsum(self,_card,_sum,_ncheck,_idtrsc):
        return self.cmd("dedsum",_card,_sum,_ncheck,_idtrsc)

    def cmd_closesum(self,_card):
        return self.cmd("closesum",_card)

