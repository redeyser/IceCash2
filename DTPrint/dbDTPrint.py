#!/usr/bin/python
# -*- coding: utf-8
# version 1.002
# DataBase for Driver Thermal Printer
import my
import os
import re
from md5 import md5
import tbDTPrint as tbs

DATABASE = "DTPrint"
MYSQL_USER = "dtprint"
MYSQL_PASSWORD = "dtprint2048"

TYPE_CONNECT = ['SERIAL','USB','NET']
TYPE_DEVICE  = ['ESCPOS','ESCPOS_OLD','KKM_FPRINT','KKM_SHTRIHM']

class dbDTPrint(my.db):
    def __init__(self,dbname,host,user,password):
        my.db.__init__(self,dbname,host,user,password)
        self.tb_sets      = tbs.tb_sets ('tp_sets')
        self.tb_logs      = tbs.tb_logs ('tp_logs')
        self.tb_printers  = tbs.tb_printers ('tp_printers')

    def _log(self,ip,user,cmd,url,xml,result=0):
        self.run(self.tb_logs._add([ip,user,cmd,url,xml,result]));
    

    def _read_sets(self):
        self.sets={}
        data = self.get(self.tb_sets._getall())
        for d in data:
            self.sets[d[1]]=d[2]
                
    def _packid(self):
        n=0
        prn=self.get(self.tb_printers._get())
        for p in prn:
            n=n+1
            self.run(self.tb_printers._newid(p[0],n))


    def _create(self):
        if self.open():
            self.run("drop database %s" % DATABASE)
            self.run("create database %s" % DATABASE)
            self.run("create user 'dtprint'@'localhost' IDENTIFIED BY 'dtprint2048'")
            self.run("grant all on "+DATABASE+".* to 'dtprint'@'localhost'")
            self.run("flush privileges")
            self.run("use %s" % DATABASE)
            self.run(self.tb_sets._create())
            self.run(self.tb_sets._add(['server_ip','']))
            self.run(self.tb_sets._add(['server_port','10111']))
            self.run(self.tb_sets._add(['password_adm',md5("dtpadm").hexdigest()]))
            self.run(self.tb_sets._add(['password_usr',md5("usr").hexdigest()]))

            self.run(self.tb_logs._create())
            self.run(self.tb_logs._add(['localhost','adm','INSTALL','/','',0]))
            self.run(self.tb_printers._create())
            print "created database"
        else:
            print "error.not_open"


