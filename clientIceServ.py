#!/usr/bin/python
# -*- coding: utf-8

"""
    Web Client for IceServ
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
"""
import httplib, urllib
from dIceCash import PATH_DOWNLOAD_PRICE, PATH_DOWNLOAD,VERSION
import my
import json
import os

_LIMIT=100

class IceServClient:

    def __init__(self,db,site="site"):
        self.db=db
        self.site=site
        self.server_port=int(self.db.sets['backservice_port'])
        self.server_ip=self.db.sets['backoffice_ip']
        self.regid=self.db.sets['regid']
        self.password=self.db.sets['regpassword']
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


    def get_file(self,page,fn):
        return urllib.urlretrieve(page, fn)

    def get(self,_type,page,params):
        self.data=""
        #print _type,page,params
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

    def get_myprice(self):
        return self.get('GET','/cmd/myprice',{'regid':self.regid,'idplace':self.idplace,'nkassa':self.nkassa})

    def set_myprice(self):
        dt=my.curdate2my()
        tm=my.curtime2my()
        self.db._sets_upd('pricenum',dt+" "+tm)
        return self.get('GET','/cmd/myprice/set',{'regid':self.regid,'idplace':self.idplace,'nkassa':self.nkassa})

    def download_price(self,fn):
        path=self.site+"%s/%s.zip" % (PATH_DOWNLOAD_PRICE,fn)
        if self.get('GET','/files/download/price/%s_%s.zip' % (self.regid,fn),{}):
            f=open(path,"wb")
            f.write(self.data)
            f.close()
            return True
        else:
            return False

    def send_zet(self,jZet):
        return self.get('POST','/cmd/Zet/send',{'regid':self.regid,'idplace':self.idplace,'nkassa':self.nkassa,'data':jZet})

    def send_trsc(self,jtrsc):
        try:
            f=open("/opt/IceCash/id.txt","r")
            id=f.readline()
            f.close()
            id=int(id)
        except:
            id=0
        return self.get('POST','/cmd/trsc/send',{'regid':self.regid,'idplace':self.idplace,'nkassa':self.nkassa,'data':jtrsc,'version':VERSION,'upgrade':id,'prn_name':self.db.sets['d_name'],'prn_type':self.db.sets['d_devtype']})

    def transport_zets(self):
        self.db._Zet_gets(None,None,up=0)
        if len(self.db.Zets)==0:
            return 0
        i=0
        J=[]
        for zet in self.db.Zets:
            if not self.db._Zet_get(int(zet['id'])):
                continue
            J.append( {'head':self.db.Zet,'body':self.db.Zet_ct} )
            i+=1
            if i>_LIMIT:
                break
        jZet = json.dumps( J )
        if not self.send_zet(jZet):
            return 0
        d=json.loads(self.data)
        for id in d:
            self.db._Zet_upd(id,{'up':1})
        return len(d)
        
        
    def transport_trsc(self):
        d=self.db._trsc_get(None,_LIMIT*10)
        jtrsc=json.dumps(d,ensure_ascii=False)
        if not self.send_trsc(jtrsc.encode("utf8")):
            return False
        d=json.loads(self.data)
        if type(d)==int and d==0:
            return False
        if len(d)!=2:
            return False
        id1=d[0]
        id2=d[1]
        if not self.db._trsc_updup(id1,id2,1):
            return False
        return True

    def get_actions(self):
        if self.get('GET','/cmd/actions',{'regid':self.regid,'idplace':self.idplace,'curaction':self.db.sets['action']}):
            data=json.loads(self.data)
            if len(data['actions'])==0:
                return False
            self.db._sets_upd('action',str(data['id']))
            self.db.run(self.db.tb_actions_hd.query_truncate())
            self.db.run(self.db.tb_tlist.query_truncate())
            for a in data['actions']:
                self.db.run(self.db.tb_actions_hd._add(a))
            #print data['tlists']
            for k,v in data['tlists'].items():
                for idt in v:
                    self.db.run(self.db.tb_tlist._add(k,idt))
            return True
        else:
            return False

    def get_regs_sets(self):
        if self.get('GET','/cmd/regs_sets',{'regid':self.regid,'cursets':self.db.sets['sets']}):
            data=json.loads(self.data)
            if len(data['sets'])==0:
                return False
            self.db._sets_upd('sets',str(data['id']))
            for k,v in data['sets'].items():
                if not self.db.sets.has_key(k):
                    self.db._sets_add('magazine',k,v)
                self.db._sets_upd(k,v)
            return True
        else:
            return False

    def download_file(self,ffrom,fto,fname):
        path=self.site+"/files/%s" % (fto+fname)
        if self.get('GET','/files/%s' % (ffrom+fname),{}):
            try:
                f=open(path,"wb")
                f.write(self.data)
                f.close()
            except:
                return False
            return True
        else:
            return False

    def download_upgrade_prog(self,fn):
        ffrom="download/upgrade/" 
        fto  ="download/" 
        path=self.site+"/files/%s" % (fto+fn)
        if self.download_file(ffrom,fto,fn):
            os.system("cd .. && mv dIceCash _dIceCash_%s && tar -xpjf _dIceCash_%s/%s" % (VERSION,VERSION,path))
            return True
        else:
            return False

    def download_upgrade_base(self,id,idlast):
        ffrom="script/" 
        fto  ="script/" 
        path=self.site+"/files/script/"
        r=True
        for s in range(id+1,idlast+1):
            fn = "iceupd_%s.tar.bz2" % str(s).rjust(3,"0")
            if self.download_file(ffrom,fto,fn):
                os.rename("/home/kassir/dIceCash/"+path+fn,"/opt/IceCash/upgrades/"+fn)
            else:
                r=False
                break
        return r
