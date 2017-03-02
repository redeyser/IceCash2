#!/usr/bin/python
# -*- coding: utf-8

"""
    Web Client for IceServ
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
"""
import httplib, urllib
import my
import json
import os

_LIMIT=100

class IceRestClient:

    def __init__(self,db):
        self.db=db
        self.server_port=int(self.db.sets['server_port'])+2
        self.server_ip=self.db.sets['icerest_ip']
        self.idplace=self.db.sets['idplace']
        self.nkassa=self.db.sets['nkassa']

    def connect(self):
        #print "connect:",self.server_ip,self.server_port
        try:
            self.conn = httplib.HTTPConnection("%s:%d" % (self.server_ip,self.server_port))
            return True
        except:
            print "not connect"
            return False

    def get(self,_type,page,params):
        self.data=""
        #print _type,page,params
        if not self.connect():
            print "error connect"
            return False
        if _type=='GET':
            p='_user=kassa1&_password=1'
            for k,v in params.items():
                if p!='':
                    p+='&'
                p+="%s=%s" %(k,v)
            page=page+"?"+p
        params=urllib.urlencode(params)
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/xml"}
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

    def get_zakaz_list(self):
        if not self.get('GET','/zakaz/list',{}):
            return False
        self.zakaz=json.loads(self.data)
        return True

    def block_zakaz(self,id):
        if not self.get('GET','/zakaz/block',{'id':id}):
            return False
        d=json.loads(self.data)
        return d['result']

    def unblock_zakaz(self,id):
        if not self.get('GET','/zakaz/block',{'id':id,'unblock':1}):
            return False
        d=json.loads(self.data)
        return d['result']

    def clear_zakaz(self,id):
        if not self.get('GET','/zakaz/clear',{'id':id}):
            return False
        d=json.loads(self.data)
        return d['result']

