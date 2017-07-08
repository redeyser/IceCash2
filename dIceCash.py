#!/usr/bin/python
# -*- coding: utf-8

"""
    Web Kassa IceCash 2.0
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
"""

from   BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from   SocketServer import ThreadingMixIn
from   fhtml import *
from   md5 import md5
import threading
import urlparse
import cgi
import Cookie
import time
import sys,os
import re
import json
import subprocess
PIPE = subprocess.PIPE
import my

#from dbIceCash import TB_EGAIS_PLACES,TB_EGAIS_OSTAT,TB_EGAIS_DOCS_HD,TB_EGAIS_DOCS_CT
import dbIceCash as db
from clientDrv import DTPclient
from chIceCash import *
from zIceCash import *
from clientIceRest import *
from clientIceServ import *
from clientEgais import *
from chIceCash import _round

MYSQL_HOST  = 'localhost'
VERSION     = '2.0.079'

RULE_NO         = -1
RULE_SELLER     = 10
RULE_KASSIR     = 50
RULE_ADMIN      = 100

POST_TRUE       = "1"
POST_FALSE      = "0"

CMD_ERROR       = "1"
_RESULT         = 'result'
_ID             = 'id'

PATH_DOWNLOAD_PRICE = "/files/download/price"
PATH_DOWNLOAD = "/files/download"

def gethash(h,key,default):
    if h.has_key(key):
        return h[key]
    else:
        return default


#def ice_create_lock ():
icelock=threading.Lock()

def ice_lock():
    icelock.acquire()

def ice_unlock():
    icelock.release()

def lsdir(dir):
    f=[]
    d=[]
    for (dirpath, dirnames, filenames) in os.walk(dir):
        f.extend(filenames)
        d.extend(dirnames)
        break
    return [d,f]

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

def startservice(cmd):
    p = subprocess.Popen(cmd, shell=True, stdout=PIPE)

def json_serial_str(obj):
    """JSON serializer for objects not serializable by default json code"""
    return str(obj)
        
class Handler(BaseHTTPRequestHandler):

    def mysql_open(self):
        self.db = db.dbIceCash(db.DATABASE, MYSQL_HOST, db.MYSQL_USER, db.MYSQL_PASSWORD) 
        return self.db.open()
        
    def _getval(self,key,default):
        if self.get_vals.has_key(key):
            return self.get_vals[key]
        else:
            return default

    def _send_HEAD(self,tp,code=200):
        self.send_response(code)
        self.send_header("Content-type", tp)
        self.end_headers()

    def _send_redirect(self,url):
        self.send_response(302)
        self.send_header('Location', url)

    def _redirect(self,url):
        self._send_redirect(url)
        self.end_headers()

    def do_HEAD(self):
        self._send_HEAD('text/html')
        self.send_response(200)

    def ReadCookie(self):
        if "Cookie" in self.headers:
            c = Cookie.SimpleCookie(self.headers["Cookie"])
            if c.has_key('Icelogin') and c.has_key('Icepassword'):
                self.curlogin    = c['Icelogin'].value
                self.curpassword = c['Icepassword'].value
                return True
            else:
                self.curlogin    = None
                self.curpassword = None
                return False

    def GetAuth(self,gets):
        if gets.has_key("_user") and gets.has_key("_password"):
            self.curlogin    = gets['_user']
            self.curpassword = gets['_password']
            return True
        else:
            return False
            
    def PostAuth(self,form):
        if form.has_key("_user") and form.has_key("_password"):
            self.curlogin    = form['_user'].value
            self.curpassword = form['_password'].value
            return True
        else:
            return False

    def WriteCookie(self,form):
        if form.has_key("login"):
            c = Cookie.SimpleCookie()
            c['Icelogin'] = form["login"].value
            c['Icepassword'] = form["password"].value
            self.send_header('Set-Cookie', c.output(header=''))

    def ClearCookie(self):
        c = Cookie.SimpleCookie()
        c['Icelogin'] = ""
        c['Icepassword'] = ""
        self.send_header('Set-Cookie', c.output(header=''))

    def get_file(self,path="",decode=True):
        if path[0]!='/':
            path='/'+path
        path=self.site+path
        try:
            f=open(path,"r")
            message=f.read()
            f.close()
        except:
            message=''
        if decode:
            message=message.decode("utf8")
        return message

    def put_file(self,filedata,path):
        path=self.site+path
        try:
            f=open(path,"w")
            f.write(filedata)
            f.close()
            return True
        except:
            return False
            pass
        return 
    
    def pattern_params_get(self,html):
        params={}
        a=re.findall("%%#.*?#.*?%%",html)
        for n in a:
            m=re.search("%%#(.*?)#(.*?)%%",n)
            if m!=None and len(m.groups())==2:
                tag=m.group(1)
                params[tag]=m.group(2)
        return params

    def pattern_rep_arr(self,html,amark,aval):
        return ht_reptags_arr(html,amark,aval)

    def pattern_rep_hash(self,html,h):
        return ht_reptags_hash(html,h)

    def pattern_params_clear(self,html):
        a=re.findall("%%#.*?#.*?%%",html)
        for n in a:
            html=html.replace(n,"")
        a=re.findall("%.*?%",html)
        for n in a:
            html=html.replace(n,"")
        return html

    def _writetxt(self,html):
        self._send_HEAD("text/html")
        self.wfile.write(html.encode("utf8"))

    def _writejson(self,j):
        self._send_HEAD("application/json")
        self.wfile.write(j.encode("utf8"))

    def write_body(self,b):
        html=self.get_file('/head.html')
        info_user=self.curlogin
        info_ip=self.client_address[0]
        regcode=self.db.sets["regid"]
        placename=self.db.sets["placename"]
        html = ht_reptags_arr(html,["%css%","%body%"],[self.cur_css,b])
        html = ht_reptags_arr(html,["%regcode%","%version%","%info_user%","%info_ip%","%info_currule%","%placename%","%idplace%","%nkassa%"],[regcode,VERSION,info_user,info_ip,str(self.currule),placename,str(self.db.idplace),str(self.db.nkassa)])
        self._writetxt(html)

    def wbody(self,p):
        self.write_body(self.replace_rulehid(p))

    def _request(self,rule,pattern,alter):
        if self.currule<rule:
            self._redirect(alter)
            return
        self.wbody(pattern)

    def write_file(self,f):
        self._send_HEAD("application/x")
        html=self.get_file(f,False)
        self.wfile.write(html)

    def verify(self):   
        if self.db._user_auth(self.curlogin,self.curpassword):
            if self.db.user['css']!='':
                self.cur_css=self.db.user['css']
            self.currule=self.db.user['type']
            self.iduser=self.db.user['id']
            return True
        else:
            return False

    def replace_rulehid(self,p):
        if self.currule < RULE_KASSIR:
            hid_kassir="hidden"
        else:
            hid_kassir=""
        if self.currule < RULE_ADMIN:
            hid_admin ="hidden"
        else:
            hid_admin=""
        return self.pattern_rep_arr(self.get_file(p),["%hid_nokassir%","%hid_noadmin%"],[hid_kassir,hid_admin])

    def create_dtp(self):
        self.dtpclient=DTPclient(self.db.sets["dtprint_ip"],int(self.db.sets["dtprint_port"]),self.db.sets["dtprint_passwd"])
        if self.db.sets.has_key('d_ignore') and self.db.sets['d_ignore']=='1':
            self.dtpclient.err_ignore=True
        else:
            self.dtpclient.err_ignore=False
        if self.db.sets.has_key('d_autocut') and self.db.sets['d_autocut']=='1':
            self.dtpclient.use_cut=True
        else:
            self.dtpclient.use_cut=False

    def create_check(self):
        self.check=chIceCash(self.db,self.iduser)

    def create_zet(self):
        self.zet=zIceCash(self.db)

    def create_iceserv(self):
        self.iceserv=IceServClient(self.db,self.site)

    def create_egais(self):
        self.egais=EgaisClient(self.db.sets["egais_ip"],8080,self.db)

    def create_icerest(self):
        self.icerest=IceRestClient(self.db)

    def cur_check_json(self):
        self.check._load_cur()
        ch=self.db._check_json()
        return json.dumps(ch,ensure_ascii=False)

    def qstd_gets(self,table,where="",fields=None,order=None,group=None,tohash=False,toarr=False,usegets=False,nofields=False):
        if usegets:
            data=self.db._gets( table )
        else:
            data=self.db._select(table,where=where,fields=fields,group=group,order=order,tohash=tohash,toarr=toarr,nofields=nofields)
        if fields==None:
            fields=self.db.tbs[table].fieldsorder
        j=json.dumps({_RESULT:True,'fields':fields,'data':data,'order':self.db.result_order},default=json_serial_str,ensure_ascii=False)
        self._writejson(j)
        return True

    def return_true(self):
        j=json.dumps({_RESULT:True})
        self._writejson(j)
        return True

    def return_false(self):
        j=json.dumps({_RESULT:False})
        self._writejson(j)
        return True

    def upload_price(self,f):
        print "upload_file: [%s]" % f

        r=f.rfind('.')
        if r==-1:
            ext=""
        else:
            ext=f[r+1:]

        path=self.site+PATH_DOWNLOAD_PRICE
        if ext=="zip":
            cmd="unzip -xod %s %s/%s" % (path,path,f)
            ps = subprocess.Popen(cmd, shell=True, stdout=PIPE)
            while ps.poll()==None:
                pass
            out=ps.stdout.read()
            ps.communicate()
            result=ps.returncode
            ind=out.rfind('inflating:')
            fn=out[ind+11:].rstrip("\n").rstrip(" ")
            print "unzip file: [%s]" % fn
            fn=os.path.basename(fn)
            if int(result)!=0:
                return False
            os.remove("%s/%s" % (path,f))
            r=fn.rfind('.')
            f=fn

        if r==-1:
            base=f
        else:
            base=f[:r]

        a=base.split("_")
        if len(a)<2:
            print "failed format file"
            os.remove("%s/%s" % (path,f))
            return False
        (regid,price)=a
        if self.db.sets['regid']!=regid:
            print "failed regid",regid,price
            os.remove("%s/%s" % (path,f))
            return False

        dt=my.curdate2my()
        tm=my.curtime2my()
        if self.db.price_load(path+"/"+f):
            self.db._sets_upd('pricenum',dt+" "+tm)
            return True
        else:
            return False

    def print_report(self,printer,z=False):
        if z:
            _h0=u" #"+str(self.db.Zet['number'])
            _h1=u"С ГАШЕНИЕМ"
            _h2=u"IceCash Z-ОТЧЕТ"
        else:
            _h0=""
            _h1=u"БЕЗ ГАШЕНИЯ"
            _h2=u"IceCash X-ОТЧЕТ"
        self.dtpclient._cm(printer,"prn_lines",{'text':self.db.sets["orgname"]+u"\nИНН "+self.db.sets["inn"],"width":0,"height":0,"font":1,"bright":0,"big":0,"invert":0})
        self.dtpclient._cm(printer,"prn_lines",{'text':self.db.sets["placename"]+u"\nКПП "+self.db.sets["kpp"],"width":0,"height":0,"font":1,"bright":10,"big":0,"invert":0})
        self.dtpclient._cm(printer,"prn_lines",{'text':u"ОТЧЕТ СУТОЧНЫЙ"+_h0,"width":0,"height":0,"font":1,"bright":10,"big":1,"invert":1,"align":"centers"})
        self.dtpclient._cm(printer,"prn_lines",{'text':_h1,"width":0,"height":0,"font":1,"bright":10,"big":1,"invert":1,"align":"centers"})

        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Продаж:","value":_round(float(self.db.Zet['summa']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Скидок:","value":_round(float(self.db.Zet['discount']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Бонусных скидок:","value":_round(float(self.db.Zet['bonus_discount']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"ВЫРУЧКА:","value":_round(float(self.db.Zet['vir']),2),"ch":".","bold":1})
        self.dtpclient._cm(printer,"prn_line", {'ch':u"-"})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Наличкой:","value":_round(float(self.db.Zet['summa_nal']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Кредитом:","value":_round(float(self.db.Zet['summa_bnal']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_line", {'ch':u"-"})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Возвратов:","value":_round(float(self.db.Zet['summa_ret']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Бонусов:","value":_round(float(self.db.Zet['bonus']),2),"ch":"."})
        self.dtpclient._cm(printer,"prn_line", {'ch':u"-"})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Чеков:","value":self.db.Zet['c_sale'],"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Возвратных:","value":self.db.Zet['c_return'],"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Отмененных:","value":self.db.Zet['c_cancel'],"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Ошибочных:","value":self.db.Zet['c_error'],"ch":"."})
        self.dtpclient._cm(printer,"prn_line", {'ch':u"-"})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Расчетная дата:","value":self.db.Zet['date'],"ch":".","bold":1})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Дата открытия смены:","value":self.db.Zet['begin_date'],"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Время открытия смены:","value":self.db.Zet['begin_time'],"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Дата закрытия смены:","value":self.db.Zet['end_date'],"ch":"."})
        self.dtpclient._cm(printer,"prn_sale_style",{'text':u"Время закрытия смены:","value":self.db.Zet['end_time'],"ch":"."})
        self.dtpclient._cm(printer,"prn_lines",{'text':_h2,"width":0,"height":0,"font":1,"bright":10,"big":1,"invert":1,"align":"centers"})
        self.dtpclient._cm(printer,"_beep",{})
        self.dtpclient._cm(printer,"_cut",{'type':0})

    """ GET REQUEST 
        ------------
    """    

    def do_GET(self):
        self.cur_css='blue.css'
        parsed_path = urlparse.urlparse(self.path)
        getvals=parsed_path.query.split('&')
        self.get_vals={}

        try:
            for s in getvals:
                if s.find('=')!=-1:
                    (key,val) = s.split('=')
                    self.get_vals[key] = val
        except:
            print "error get!"
            self.get_vals={}
                
        self.currule=RULE_NO

        if not self.mysql_open():
            self._send_HEAD("text/html",404)
            return
        else:
            self.db._read_sets()

        if not self.db.sets.has_key('icerest_ip'):
            self.db._sets_add('server','icerest_ip','localhost')
        if not self.db.sets.has_key('d_ncheck'):
            self.db._sets_add('device','d_ncheck','1')
        if not self.db.sets.has_key('site'):
            self.db._sets_add('client','site','site')
        if not self.db.sets.has_key('d_ofd'):
            self.db._sets_add('device','d_ofd','0')
            self.db._read_sets()
        
        #self.db.sets['d_name']='fprint'
        #self.db.sets['d_devtype']='KKM_FPRINT'

        self.site=self.db.sets['site']
        if not os.path.isdir(self.db.sets['site']):
            self.site='site'

        #if self.path.find(".html")!=-1:
        #    self._send_HEAD("text/html",404)
        #    return

        if self.path.find(".woff")!=-1:
            self._send_HEAD("application/x-font-woff",200)
            message=self.get_file(self.path)
            self.self.wfile.write(message)
            return
        if self.path.find(".js")!=-1:
            message=self.get_file(self.path)
            self._writetxt(message)
            return
        if self.path.find(".css")!=-1:
            message=self.get_file(self.path)
            self._writetxt(message)
            return



        if self.path=='/login':
            self.iduser=0
            self.curlogin=""
            self.currule=RULE_NO
            self.wbody("/login.html")
            return

        if not self.ReadCookie():
            if not self.GetAuth(self.get_vals):
                self._redirect("/login")
                return

        self.GetAuth(self.get_vals)

        if not self.verify():
            self._redirect("/login")
            print "not verify"
            return

        if (self.path.find("/unlogin")==0):
            self._send_redirect("/login")
            self.ClearCookie()
            self.end_headers()
            return

        """ GET SIMPLE REQUEST
            ------------------
        """    
        if self.path=='/':
            self.wbody("/index.html")
            return

        if self.path.find("/template/")!=-1:
            h=self.get_file(self.path)
            self._writetxt(h)
            return

        if self.path=='/help':
            self._request(RULE_SELLER,"/help.html","/")
            return

        if self.path=='/ot':
            self._request(RULE_KASSIR,"/ot.html","/")
            return

        if self.path=='/ot/Zet':
            self._request(RULE_KASSIR,"/otZ.html","/")
            return

        if self.path=='/ot/check':
            self._request(RULE_KASSIR,"/otcheck.html","/")
            return

        if self.path=='/service':
            self._request(RULE_KASSIR,"/service.html","/")
            return

        if self.path=='/sets':
            self._request(RULE_KASSIR,"/sets.html","/")
            return

        if self.path=='/sets_driver':
            self._request(RULE_KASSIR,"/sets_driver.html","/")
            return
        if self.path.find('/help')!=-1:
            if not self.get_vals.has_key('id'):
                self._writetxt(POST_FALSE)
                return
            self._request(RULE_SELLER,self.get_vals['id']+".html","/")
            return

        if parsed_path.path=='/reg/menu':
            if not self.get_vals.has_key('menu'):
                self.wfile.write(POST_FALSE)
            self.wbody("/regm"+self.get_vals['menu']+".html")
            return

        """ GET  < E G A I S >
            ------------------
        """    
        if parsed_path.path=='/egais':
            self.create_egais()
            if self.egais._connect():
                c=u"<span class='green norm'>УТМ работает</span><br><span class='flame norm'>%s</span>" % self.egais.fsrar_id
                online='egais_connected'
            else:
                online='egais_disconnected'
                c=u"УТМ не работает"
            html=self.get_file("/egais.html")
            html=self.pattern_rep_arr(html,["%connect%","%online%"],[c,online])
            self.write_body(html)
            del self.egais
            return

        if parsed_path.path=='/egais/get/mydocs':
            postav=self._getval('postav',None)
            status=self._getval('status',None)
            _type=self._getval('type',None)
            dt1=self._getval('dt1',None)
            dt2=self._getval('dt2',None)
            if status!=None:
                status=int(status)
            if _type==None:
                _type=0
            docs=self.db.egais_get_mydocs(_type,status,postav,dt1,dt2)
            j=json.dumps(docs,ensure_ascii=False)
            self._writejson(j)
            return

        if parsed_path.path=='/egais/get/nattn':
            return self.qstd_gets(db.TB_EGAIS_DOCS_NEED,tohash=False,usegets=True)
            #docs=self.db._select(db.TB_EGAIS_DOCS_NEED)
            #print docs
            #j=json.dumps(docs,ensure_ascii=False)
            #self._writejson(j)
            #return

        if parsed_path.path=='/egais/get/doc':
            idd=self._getval('idd',0)
            if idd==0:
                return_false()
                return
            fd=['id','pref_AlcCode','oref_ShortName','pref_ShortName','pref_AlcVolume','pref_Capacity','wbr_InformBRegId','pref_ProductVCode','real_Quantity','pref_RegId']
            hd=self.db._select(db.TB_EGAIS_DOCS_HD,"id=%s" % idd,None,tohash=False,nofields=False)
            if len(hd)>0:
                hd=hd[0]
            ct=self.db._select(db.TB_EGAIS_DOCS_CT,"iddoc=%s" % idd,fd,order="wb_Identity",tohash=False,nofields=True)
            j=json.dumps({_RESULT:'true','hd':hd,'ct':ct,'fields':fd},default=json_serial_str,ensure_ascii=False)
            self._writejson(j)
            return

        if parsed_path.path=='/egais/get/mydoc':
            idd=self._getval('idd',0)
            self.db.egais_get_mydoc(int(idd))
            j=json.dumps({'hd':self.db.egais_doc_hd,'ct':self.db.egais_doc_ct},ensure_ascii=False)
            self._writejson(j)
            return
        #print parsed_path.path
        if parsed_path.path=='/egais/get/docs':
            print "egais:get_docs"
            self.create_egais()
            if not self.egais._connect():
                print "egais:not connect"
                self._writetxt(POST_FALSE)
                return False
            if not self.egais._get_docs_in():
                print "egais:not get docs"
                self._writetxt(POST_FALSE)
                return
            self.egais._get_docs_out()
            res=self.egais._dodoc()
            j=json.dumps({'data_url':self.egais.data_url,'result':res},ensure_ascii=False)
            self._writejson(j)
            del self.egais
            return

        if parsed_path.path=='/egais/get/ostats':
            fd=['id','pref_AlcCode','oref_ShortName','pref_FullName','pref_AlcVolume','pref_Capacity','rst_InformBRegId','pref_ProductVCode','rst_Quantity','rst_InformARegId']
            return self.qstd_gets(db.TB_EGAIS_OSTAT,"",fd,order="oref_ClientRegId,pref_AlcCode",tohash=False,nofields=True)

        if parsed_path.path=='/egais/get/ostat':
            ostat=self.db.egais_get_ostat()
            data=[]
            for r in ostat:
                l=[]
                for f in r:
                    l.append(unicode(f))
                data.append(l)
            j=json.dumps(data,ensure_ascii=False)
            self._writejson(j)
            return

        if parsed_path.path=='/egais/send/docs':
            self.create_egais()
            docs=self.db.egais_get_mydocs(0,2,None,None,None)
            i=0
            err1=""
            err2=""
            err3=""
            for d in docs:
                if self.egais._send_act(int(d['id'])):
                    i+=1
                else:
                    err1=self.egais.data
            docs=self.db.egais_get_mydocs(1,2,None,None,None)
            for d in docs:
                if self.egais._send_return(int(d['id'])):
                    i+=1
                else:
                    err2=self.egais.data
            docs=self.db.egais_get_mydocs(2,2,None,None,None)
            for d in docs:
                if self.egais._send_move(int(d['id'])):
                    i+=1
                else:
                    err3=self.egais.data
            if i==0:
                self._writetxt(err1+"<br>"+err2+"<br>"+err3)
            else:
                self._writetxt(str(i))
            del self.egais
            return

        if parsed_path.path=='/egais/get/postav':
            postav=self.db.egais_get_postav()
            j=json.dumps(postav,ensure_ascii=False)
            self._writejson(j)
            return

        if parsed_path.path=='/egais/send/places':
            self.create_egais()
            if not self.egais._send_places():
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.egais
            return

        if parsed_path.path=='/egais/get/places':
            id=self._getval('id',None)
            if id==None:
                return self.qstd_gets(db.TB_EGAIS_PLACES,"",["ClientRegId","KPP"],order="KPP",tohash=True)
            else:
                return self.qstd_gets(db.TB_EGAIS_PLACES,"ClientRegId=%s" % id,None,tohash=False)

        if parsed_path.path=='/egais/send/ostat':
            self.create_egais()
            if not self.egais._send_ostat():
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.egais
            return

        if parsed_path.path=='/egais/send/reply':
            ttn=self._getval('ttn',None)
            if ttn==None:
                self._writetxt(POST_FALSE)
                return
            self.create_egais()
            if not self.egais._send_reply(ttn):
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.egais
            return

        if parsed_path.path=='/egais/send/nattn':
            self.create_egais()
            if not self.egais._send_nattn():
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.egais
            return

        if parsed_path.path=='/egais/send/version':
            version=self._getval('version',1)
            self.create_egais()
            if not self.egais._send_version(version):
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.egais
            return

        if parsed_path.path=='/egais/create/return':
            id=self._getval('id',None)
            idd=self._getval('idd',None)
            if id==None:
                self._writetxt(POST_FALSE)
                return
            self.create_egais()
            if not self.egais._create_return(int(id),int(idd)):
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.egais
            return

        """ GET DTP REQUEST
            ------------------
        """    

        if self.path=='/cmd/status':
            self.create_zet()
            self.zet._calc(False)
            del self.zet
            if self.db.Zet['vir']!=0:
                f_opensm="True"
            else:
                f_opensm="False"
            if self.db.sets.has_key("temperature"):
                temp=self.db.sets['temperature']
            ncheck=self.db._trsc_last()
            status={'c_sum':self.db.Zet['vir'],'f_opensm':f_opensm,'sum_nal':self.db.Zet['summa_nal'],'sum_bnal':self.db.Zet['summa_bnal'],'c_check':ncheck+1,'temperature':temp}
            self._writejson(json.dumps(status))
            return

        if self.path=='/cmd/prn_devstatus':
            printer=self.db.sets["d_name"]
            if printer=='None':
                self._writetxt(POST_FALSE)
                return
            self.create_dtp()
            if not self.dtpclient._cmd_prn_devstatus(printer):
                self._writetxt(self.dtpclient.result_name)
            else:
                self._writejson(json.dumps(self.dtpclient.return_data))
            del self.dtpclient
            return

        if self.path=='/cmd/prn/openbox':
            printer=self.db.sets["d_name"]
            if printer=='None':
                self._writetxt(POST_FALSE)
                return
            self.create_dtp()
            if not self.dtpclient._cm(printer,"_openbox",{}):
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.dtpclient
            return

        if self.path=='/cmd/prn/opensmena':
            printer=self.db.sets["d_name"]
            if printer=='None':
                self._writetxt(POST_FALSE)
                return
            self.create_dtp()
            if not self.dtpclient._cm(printer,"_opensmena",{}):
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.dtpclient
            return

        if self.path=='/cmd/prn/continuePrint':
            printer=self.db.sets["d_name"]
            if printer=='None':
                self._writetxt(POST_FALSE)
                return
            self.create_dtp()
            if not self.dtpclient._cm(printer,"_continueprint",{}):
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            del self.dtpclient
            return

        """ GET USER
            ------------------
        """ 

        if parsed_path.path=='/user':
            if self.currule<=RULE_SELLER:
                self._redirect("/")
                return
            if not self.get_vals.has_key('iduser'):
                self._redirect("/")
                return
            if not self.db._user_get(id=int(self.get_vals['iduser'])):
                self.db.user=self.db.tb_users._clear()
            html=self.pattern_rep_hash(self.get_file("/ed_user.html"),self.db.user)
            types=self.db._types_get("us")
            types_select = ht_db2select(types,1,2,self.db.user['type'])
            html=self.pattern_rep_arr(html,["%types_select%"],[types_select])
            self._writetxt(html)
            return

        if self.path=='/users':
            if self.currule<=RULE_SELLER:
                self._redirect("/")
                return
            users=self.db._user_gets(self.currule,"<=")
            html=self.get_file("/users.html")
            params=self.pattern_params_get(html)
            htable = ht_db2table(users,[0,1,8,5],0,gethash(params,'table_users',""))
            html=self.pattern_rep_arr(html,["%table_users%"],[htable])
            html=self.pattern_params_clear(html)
            self.write_body(html)
            return

        """ GET TRSC
            ------------------
        """ 
        
        if parsed_path.path=="/getup/check/list":
            idzet=self._getval('idzet',None)
            up=self._getval('up',None)
            if idzet:
                idzet=int(idzet)
            limit=self._getval('limit',None)
            if limit:
                limit=int(limit)
            d=self.db._trsc_get(idzet,limit)
            j=json.dumps(d,ensure_ascii=False)
            self._writejson(j)
            return
        
        if parsed_path.path=="/getup/check/set":
            up=self._getval('up',None)
            id1=self._getval('id1',None)
            id2=self._getval('id2',None)

            if not up:
                self._writetxt(POST_FALSE)
                return
            else:
                up=int(up)

            if not id1 or not id2:
                self._writetxt(POST_FALSE)
                return
            else:
                id1=int(id1)
                id2=int(id2)
                up=int(up)

            if not self.db._trsc_updup(id1,id2,up):
                self._writetxt(POST_FALSE)
            else:
                self._writetxt(POST_TRUE)
            return
        
        """ GET ZET
            ------------------
        """ 
        if parsed_path.path=="/ot/Zet/recalc":
            if self.get_vals.has_key('id'):
                id=int(self.get_vals['id'])
                self.create_zet()
                if not self.zet._Z_recalc(id):
                    self._writetxt(POST_FALSE)
                    del self.zet
                    return
            else:
                self._writetxt(POST_FALSE)
            self._writetxt(POST_TRUE)
            return

        if parsed_path.path=="/ot/Zet/xml":
            if self.get_vals.has_key('id'):
                id=int(self.get_vals['id'])
                self.create_zet()
                if not self.zet._get_xml(id):
                    self._writetxt(POST_FALSE)
                    del self.zet
                    return

                if not self.get_vals.has_key('save'):
                    self._writetxt(self.zet.XML_Zet)
                else:
                    fn=self.zet._save_xml()
                    self._writetxt(fn)
                del self.zet
            else:
                self._writetxt(POST_FALSE)
            return

        if parsed_path.path=="/getup/Zet/list":
            dt1=self._getval('dt1',None)
            dt2=self._getval('dt2',None)
            up=self._getval('up',None)
            xml=self._getval('xml',None)
            if up!=None:
                up=int(up)
            self.db._Zet_gets(dt1,dt2,up=up)
            if xml==None:
                j=json.dumps(self.db.Zets,ensure_ascii=False)
                self._writejson(j)
            else:
                body=""
                for hline in self.db.Zets:
                    sline=""
                    for k,v in hline.items():
                        sline+="\t<%s>%s</%s>\n" % (k,v,k)
                    x="\t<zet>\n%s</zet>\n\n" % (sline)
                    body+=x
                XML='<?xml version="1.0" encoding="UTF-8"?>\n<data type="icecash_zets">\n\n<body>\n'+body+'</body>\n\n</data>'
                self._writetxt(XML)
            return

        if parsed_path.path=="/getup/Zet/get":
            id=self._getval('id',None)
            xml=self._getval('xml',None)
            if not id:
                self._writetxt(POST_FALSE)
                return
            else:
                id=int(id)
            if not self.db._Zet_get(id):
                self._writetxt(POST_FALSE)
                return
            if xml==None:
                j=json.dumps({'head':self.db.Zet,'body':self.db.Zet_ct},ensure_ascii=False)
                self._writejson(j)
            else:
                head=""
                for k,v in self.db.Zet.items():
                    head+="\t<%s>%s</%s>\n" % (k,v,k)
                body=""
                for hline in self.db.Zet_ct:
                    sline=""
                    for k,v in hline.items():
                        sline+="\t<%s>%s</%s>\n" % (k,v,k)
                    body+="\t<tov>\n%s</tov>\n\n" % (sline)
                XML='<?xml version="1.0" encoding="UTF-8"?>\n<data type="icecash_zet">\n\n<head>\n'+head+'</head>\n\n<body>\n'+body+'</body>\n\n</data>'
                self._writetxt(XML)
                body=""
            return

        if parsed_path.path=="/getup/Zet/set":
            up=self._getval('up',None)
            id=self._getval('id',None)

            if not up:
                self._writetxt(POST_FALSE)
                return
            else:
                up=int(up)

            if not id:
                self._writetxt(POST_FALSE)
                return
            else:
                id=int(id)

            if not self.db._Zet_upd(id,{'up':up}):
                self._writetxt(POST_FALSE)
            else:
                self._writetxt(POST_TRUE)
            return

        if parsed_path.path=="/ot/Zet":
            if self.get_vals.has_key('month'):
                if self.get_vals['month']=='0':
                    cur=True
                else:
                    cur=False
                self.create_zet()
                self.zet._gets(cur)
                del self.zet
                j=json.dumps(self.db.Zets,ensure_ascii=False)
                self._writejson(j)
            elif self.get_vals.has_key('date'):
                pass
            elif self.get_vals.has_key('id'):
                id=int(self.get_vals['id'])
                self.db._Zet_get_html(id)
                j=json.dumps(self.db.Zet_ct,ensure_ascii=False)
                self._writejson(j)
            else:
                self._writetxt(POST_FALSE)
            return


        if parsed_path.path=="/ot/check":
            #print self.path
            id=self._getval('id',None)
            if id:
                if not self.db._trsc_get_check(int(id)):
                    self._writetxt(POST_FALSE)
                else:
                    j=json.dumps({'hd':self.db.trsc_hd,'ct':self.db.trsc_ct},ensure_ascii=False)
                    self._writejson(j)
                    return

            dt1=self._getval('dt1',None)
            dt2=self._getval('dt2',None)
            tm1=self._getval('tm1',None)
            tm2=self._getval('tm2',None)
            ncheck=self._getval('ncheck',None)
            tcheck=self._getval('tcheck',None)
            tpay=self._getval('tpay',None)
            tclose=self._getval('tclose',None)
            dcard=self._getval('dcard',None)
            bcard=self._getval('bcard',None)
            fiscal=self._getval('fiscal',None)
            error=self._getval('error',None)
            discount=self._getval('discount',None)
            bonus=self._getval('bonus',None)
            summa=self._getval('summa',None)
            alco=self._getval('alco',None)
            code=self._getval('code',None)
            group=self._getval('idgroup',None)
            self.db._trsc_filter(dt1,dt2,tm1,tm2,ncheck,tcheck,tpay,tclose,dcard,bcard,fiscal,error,discount,bonus,summa,alco,code,group)
            j=json.dumps(self.db.f_checks,ensure_ascii=False)
            self._writejson(j)
            return

        """ GET REGISTRATION
            ------------------
        """ 

        if self.path=='/reg/curcheck':
            self.create_check()
            try:
                ice_lock()
                self.check._load_cur()
                self.check._calc()
            finally:
                ice_unlock()
            j=self.cur_check_json()
            del self.check
            self._writejson(j)
            return

        if parsed_path.path=="/check/copy":
            id=self._getval('id',None)
            if id==None:
                _if="ispayed=1"
            else:
                _if="ispayed=1 and ncheck=%s" % id
            id=self.db._trsc_last(_if=_if)
            if id==0:
                self._writetxt(POST_FALSE)
                return

            self.create_check()
            self.create_dtp()
            self.check._init_dtp(self.dtpclient)
            if not self.check._copycheck(int(id)):
                self._writetxt(self.check.error)
                return
            self._writetxt(POST_TRUE)
            del self.dtpclient
            del self.check
            return

        if parsed_path.path=="/check/return":
            id=self._getval('id',None)
            if not id:
                self._writetxt(POST_FALSE)
                return

            self.create_check()
            try:
                ice_lock()
                self.db._trsc_to_check(self.iduser,int(id),ro=True,_reverse=True)
                #print self.db.trsc_hd
                if self.db.trsc_hd['bonus_card']!='':
                    if self.check._bs_connect():
                        self.check._bs_info(self.db.trsc_hd['bonus_card'])
                self.check._calc()
            finally:
                ice_unlock()
            self._writetxt(POST_TRUE)
            del self.check
            return


        if parsed_path.path=='/reg/otX':
            if self.db.sets["d_devtype"]=='ESCPOS' or self.db.sets["d_devtype"]=='ESCPOS_OLD':
                escpos=True
            else:
                escpos=False
            if self.get_vals.has_key("print"):
                printer=self.db.sets["d_name"]
                self.create_dtp()
                if not escpos:
                    if not self.dtpclient._cmd_reportX(printer,1):
                        self._writetxt(self.dtpclient.result_name)
                    else:
                        self._writetxt(POST_TRUE)
                else:
                    self.create_zet()
                    if self.zet._calc(False):
                        self.print_report(printer,False)
                    self._writetxt(POST_TRUE)
                    del self.zet
                del self.dtpclient
                return
            self.create_zet()
            self.zet._calc(False)
            del self.zet
            j=json.dumps(self.db.Zet,default=json_serial_str,ensure_ascii=False)
            self._writejson(j)
            return
        
        if self.path=='/reg/otZ':
            if self.db.sets["d_devtype"]=='ESCPOS' or self.db.sets["d_devtype"]=='ESCPOS_OLD':
                escpos=True
            else:
                escpos=False
            printer=self.db.sets["d_name"]
            self.create_dtp()
            if not escpos:
                """ Снимать Зет отет в любом случае """
                self.dtpclient._cm(printer,"_reportZ",{})
                #self._write(self.dtpclient.result_name)
                #del self.dtpclient
            self.create_zet()
            if not self.zet._Z():
                del self.zet
                self._writetxt(POST_FALSE)
                return
            if escpos:
                self.print_report(printer,True)
            self.dtpclient._cmd_prn_sounddw(printer)
            del self.zet
            del self.dtpclient
            self._writetxt(str(self.db.Zet['number']))
            return

        if self.path=='/reg':
            html=self.get_file("/reg.html")
            users=self.db._user_gets(RULE_SELLER,"<=")
            select_seller = ht_db2select(users,0,1,0)
            html=self.pattern_rep_arr(html,["%select_seller%","%printer%"],[select_seller,self.db.sets["d_devtype"]])
            self.write_body(html)
            return

        """ GET SETS
            ------------------
        """ 

        if parsed_path.path=='/sets_get':
            if not self.get_vals.has_key('group'):
                self._redirect("/")
                return
            sets=self.db._sets_get(group=self.get_vals['group'])
            html=self.get_file("/ed_sets.html")
            params=self.pattern_params_get(html)
            htable = ht_hash2table_input(sets,gethash(params,'table_sets_caption',""),gethash(params,'table_sets_value',""))
            html=self.pattern_rep_arr(html,["%table_sets%"],[htable])
            html=self.pattern_params_clear(html)
            self._writetxt(html)
            return

        if parsed_path.path=='/sets/autosets':
            if self.currule<RULE_ADMIN:
                self._redirect("/")
                return
            sets=self.db._sets_get(group='device')
            html=self.get_file("/autosets.html")
            html=self.pattern_rep_hash(html,sets)
            serial_devs=lsserial()
            serial_devs.insert(0,'None')
            serial_devs = ht_arrstr2select(serial_devs,self.db.sets['dev_scanner'])
            html=self.pattern_rep_arr(html,["%select_scanner%"],[serial_devs])
            html=self.pattern_params_clear(html)
            self._writetxt(html)
            return

        if parsed_path.path=='/printer':
            if self.currule<=RULE_SELLER:
                self._redirect("/")
                return
            if not self.get_vals.has_key('idprinter'):
                printer=self.db.sets["d_name"]
            else:
                printer=self.get_vals['idprinter']
            self.create_dtp()
            if not self.dtpclient._get_printers():
                self.wfile.write(POST_FALSE)
                del self.dtpclient
                return 
            self.dtpclient.printers.insert(0,"None")
            printers_select = ht_arrstr2select(self.dtpclient.printers,printer)
            html=self.get_file("/ed_device.html")
            html=self.pattern_rep_arr(html,["%printers_select%"],[printers_select])
            try:
                self.dtpclient._get_printer_info(printer)
                if self.dtpclient.printer_info['type_device'] in ('KKM_FPRINT','KKM_SHTRIHM'):
                    if self.dtpclient._cmd_prn_devstatus(printer):
                        html=self.pattern_rep_hash(html,self.dtpclient.return_data)
                self.dtpclient.printer_info['result']=self.dtpclient.result_name
                html=self.pattern_rep_hash(html,self.dtpclient.printer_info)
            except:
                pass
            finally:
                html=self.pattern_params_clear(html)
                self._writetxt(html)
                del self.dtpclient

            return

        if parsed_path.path=='/printer/status':
            if self.currule<=RULE_SELLER:
                self._redirect("/")
                return
            printer=self.db.sets["d_name"]
            self.create_dtp()
            if not self.dtpclient._get_printers():
                self.wfile.write(POST_FALSE)
                del self.dtpclient
                return 
            html=self.get_file("/devinfo.html")
            if self.dtpclient._cmd_prn_devstatus(printer):
                for k,v in self.dtpclient.return_data.items():
                    if v=='False':
                        self.dtpclient.return_data[k]=u'Нет'
                    if v=='True':
                        self.dtpclient.return_data[k]=u'Да'
            else:
                self._writetxt(self.dtpclient.result_name)
                return
            self.dtpclient.return_data['result']=self.dtpclient.result_name
            html=self.pattern_rep_hash(html,self.dtpclient.return_data)
            html=self.pattern_params_clear(html)
            self._writetxt(html)
            del self.dtpclient
            return

        if self.path=="/printer/textlines":
            if self.currule<RULE_ADMIN:
                self._redirect("/")
                return
            printer=self.db.sets['d_name']
            self.create_dtp()
            if self.db.sets['d_devtype']=='KKM_FPRINT':
                if not self.dtpclient._cmd_prn_tabgets_CHR(printer):
                    self._writetxt(self.dtpclient.result_name)
                    return
            if self.db.sets['d_devtype']=='KKM_SHTRIHM':
                if not self.dtpclient._cmd_prn_tabget_textlines(printer):
                    self._writetxt(self.dtpclient.result_name)
                    return
            html=self.get_file("/devset.html")
            params=self.pattern_params_get(html)
            td=gethash(params,'table_text_td',"")
            tin=gethash(params,'table_text_tin',"")
            table_text=ht_arr2table(self.dtpclient.return_data,"textline",td,tin)
            html=self.pattern_rep_arr(html,["%table_text%"],[table_text])
            html=self.pattern_params_clear(html)
            del self.dtpclient
            self._writetxt(html)
            return

        if parsed_path.path=="/reg/getprice":
            if not self.get_vals.has_key('parent'):
                self._writetxt(POST_FALSE)
                return
            parent=self.get_vals['parent']
            if parent=="..":
                self.db._price_get(self.db.user['cur_price'])
                parent=self.db.price['idgroup']
            if parent=="" or parent==".":
                parent=self.db.user['cur_price']
            else:
                self.db._user_upd(self.iduser,{'cur_price':parent})
            if not self.db._price_get_group(parent):
                self.db._price_get_group("0")
            j=json.dumps(self.db.price,ensure_ascii=False)
            self._writejson(j)
            return

        """ EXCHANGE ICESERV
            ------------------
        """ 
        if self.path.find('/iceserv/upgrade/prog')!=-1:
            if VERSION==self.db.sets['version']:
                #print "use last version"
                self._writetxt(POST_FALSE)
                return
            if VERSION>self.db.sets['version']:
                print "use bigest version"
                self._writetxt(POST_FALSE)
                return
            filename='dIceCash.'+self.db.sets['version']+'.tar.bz2'
            print filename
            self.create_iceserv()
            if not self.iceserv.download_upgrade_prog(filename):
                print "not file"
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            del self.iceserv
            self._writetxt(POST_TRUE)
            return

        if self.path.find('/iceserv/upgrade/base')!=-1:
            if not os.path.isdir("/opt/IceCash"):
                os.mkdir("/opt/IceCash")
                os.mkdir("/opt/IceCash/upgrades")
                os.mkdir("/opt/IceCash/execute")
            if not os.path.isfile("/opt/IceCash/id.txt"):
                f=open("/opt/IceCash/id.txt","w")
                f.write("0")
                f.close()
                id=0
            else:
                f=open("/opt/IceCash/id.txt","r")
                id=f.readline()
                f.close()
                id=int(id)
            print "current id upgrade",id
            if self.db.sets.has_key("upgrade"):
                idlast=int(self.db.sets["upgrade"])
                if idlast>id:
                    print "has new upgrades",idlast
                    self.create_iceserv()
                    if self.iceserv.download_upgrade_base(id,idlast):
                        self._writetxt(POST_TRUE)
                        print "Downloaded"
                        f=open("/opt/IceCash/id.txt","w")
                        f.write(str(idlast))
                        f.close()
                        return
            self._writetxt(POST_FALSE)
            return

        if self.path.find('/iceserv/myprice')!=-1:
            self.create_iceserv()
            if not self.iceserv.get_myprice():
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            r=self.iceserv.data
            if r=="0":
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            if not self.iceserv.download_price(r):
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            self.upload_price(r+".zip")
            self._writetxt(r)
            self.iceserv.set_myprice()
            del self.iceserv
            return

        if self.path.find('/iceserv/actions')!=-1:
            self.create_iceserv()
            if not self.iceserv.get_actions():
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            self._writetxt(POST_TRUE)
            del self.iceserv
            return

        if self.path.find('/iceserv/regs_sets')!=-1:
            #print "/iceserv/regs_sets"
            self.create_iceserv()
            if not self.iceserv.get_regs_sets():
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            self._writetxt(POST_TRUE)
            del self.iceserv
            return

        if self.path.find('/iceserv/Zet/send')!=-1:
            self.create_iceserv()
            r=self.iceserv.transport_zets()
            if r==0:
                self._writetxt(POST_FALSE)
                del self.iceserv
                return
            self.wfile.write(str(r))
            del self.iceserv
            return

        if self.path.find('/iceserv/trsc/send')!=-1:
            self.create_iceserv()
            r=self.iceserv.transport_trsc()
            if not r:
                self._writetxt(POST_FALSE)
            else:
                self._writetxt(POST_TRUE)
            del self.iceserv
            return

        """ EXCHANGE ICEREST
            ------------------
        """ 
        if self.path.find('/icerest/zakaz/list')!=-1:
            self.create_icerest()
            if not self.icerest.get_zakaz_list():
                self._writetxt(POST_FALSE)
                del self.icerest
                return
            j=json.dumps(self.icerest.zakaz)
            self._writejson(j)
            del self.icerest
            return

        if self.path.find('/icerest/zakaz/block')!=-1:
            id=self._getval('id',0)
            if id==0:
                self._writetxt(POST_FALSE)
                return
            allow=True
            try:
                ice_lock()
                self.create_icerest()
                if not self.icerest.block_zakaz(id):
                    print "error block zakaz "+str(id)
                    self._writetxt(POST_FALSE)
                    allow=False
                if allow:
                    self.create_check()
                    self.db._zakaz_copy(self.iduser,int(id))
                    self.check._calc()
                    del self.check
            finally:
                ice_unlock()
                del self.icerest
            self._writetxt(POST_TRUE)
            return

        if self.path.find('/icerest/zakaz/unblock')!=-1:
            id=self._getval('id',None)
            allow=True
            try:
                ice_lock()
                self.create_check()
                if id==None:
                    self.check._load_cur()
                    if self.db._check_pos_get(self.iduser,0,self.db.ch_head["cursor"]):
                        id=self.db.ch_cont_pos['nbox']
                    else:
                        allow=False
                    if id==0:
                        allow=False
                self.create_icerest()
                if allow and not self.icerest.unblock_zakaz(id):
                    print "error unblock zakaz "+str(id)
                    self._writetxt(POST_FALSE)
                    allow=False
                if allow:
                    self.db._zakaz_delete(self.iduser,int(id))
                    self.check._calc()
            finally:
                ice_unlock()
                del self.check
                del self.icerest
            self._writetxt(POST_TRUE)
            return

        """ GET FILES REQUEST
            ------------------
        """ 
        if self.path.find('/files/')!=-1:
            if self.currule<RULE_ADMIN:
                self._writetxt(POST_FALSE)
                return
            fn=self.path
            if not os.path.isfile(self.site+fn):
                self.send_response(404)
                self.end_headers()
                return
            self.write_file(fn)
            return

        if self.path.find('/fo/ls')!=-1:
            if self.currule<RULE_ADMIN:
                self._writetxt(POST_FALSE)
                return
            if not self.get_vals.has_key('path'):
                self._writetxt(POST_FALSE)
                return
            path=self.get_vals['path'].replace("..","")
            d=lsdir(self.site+'/files/'+path)
            d.append(path)
            xml=""
            if self.get_vals.has_key('json'):
                JSON=json.dumps(d,ensure_ascii=False)
                self._writejson(JSON)
            else:
                dirs,files,cur=d
                xml+="\t<cur>"+cur+"</cur>\n"
                for k in dirs:
                    fname=k.decode("utf8")
                    x="\t<dir>"+fname+"</dir>\n"
                    xml+=x
                for k in files:
                    fname=k.decode("utf8")
                    x="\t<file>"+fname+"</file>\n"
                    xml+=x
                XML='<?xml version="1.0" encoding="UTF-8"?>\n<data type="icecash_uplist">\n\n<body>\n'+xml+"</body>\n\n</data>"
                self._writetxt(XML)
            return

        if self.path.find('/fo/rm')!=-1:
            if self.currule<RULE_ADMIN:
                self._writetxt(POST_FALSE)
                return
            if not self.get_vals.has_key('path'):
                self._writetxt(POST_FALSE)
                return
            path=self.get_vals['path'].replace("..","")
            fn=self.site+'/files/'+path
            try:
                os.remove(fn)
                self._writetxt(POST_TRUE)
            except:
                self._writetxt(POST_FALSE)
            return

        """ GET UTILS
            ------------------
        """ 
        if self.path.find('/sys/truncate_trsc')!=-1:
            if self.currule<RULE_ADMIN:
                self._writetxt(POST_FALSE)
                return
            self.db.truncate_trsc()
            self._writetxt(POST_TRUE)
            return

        if self.path.find('/sys/truncate_egais')!=-1:
            if self.currule<RULE_ADMIN:
                self._writetxt(POST_FALSE)
                return
            self.db.truncate_egais()
            os.removedirs("/opt/utm/transport/transportDB")
            self._writetxt(POST_TRUE)
            return

        if self.path.find('/sys/poweroff')!=-1:
            if self.currule<RULE_KASSIR:
                self._writetxt(POST_FALSE)
                return
            os.system("poweroff")
            self._writetxt(POST_TRUE)
            return

        if self.path.find('/sys/reboot')!=-1:
            if self.currule<RULE_KASSIR:
                self._writetxt(POST_FALSE)
                return
            os.system("reboot")
            self._writetxt(POST_TRUE)
            return

        if self.path.find('/sys/restart_utm')!=-1:
            os.system("service updater restart && sleep 3 && service utm restart")
            self._writetxt(POST_TRUE)
            return
    """ POST REQUEST 
        ------------
    """    
    
    def do_POST(self):
        self.cur_css='blue.css'
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        
        if not self.mysql_open():
            self._send_HEAD("text/html",404)
            print "error. not open mysql"
            return
        else:
            self.db._read_sets()

        #self.db.sets['d_name']='fprint'
        #self.db.sets['d_devtype']='KKM_FPRINT'

        if (self.path.find("/login")==0):
            self._send_redirect("/")
            self.WriteCookie(form)
            self.end_headers()
            return

        if not self.ReadCookie():
            if not self.PostAuth(form):
                self._redirect("/login")
                return

        self.PostAuth(form)

        if not self.verify():
            self._redirect("/login")
            return

        if self.path=="/user":
            if self.currule<=RULE_SELLER:
                self._redirect("/")
                return
            if form.has_key("id"):
                if form.has_key("save"):
                    if self.currule<RULE_ADMIN and form.has_key("type") and int(form['type'].value)>RULE_KASSIR:
                        form['type'].value=''
                    if int(form['id'].value)==0:
                        self.db.run(self.db.tb_users._add_post(form))
                    else:
                        self.db.run(self.db.tb_users._upd_post(int(form['id'].value),form))
                if form.has_key("delete"):
                    if self.currule>=RULE_ADMIN:
                        self.db.run(self.db.tb_users._del(int(form['id'].value)))
            self._send_redirect("/users")
            self.end_headers()
            return

        if self.path=="/sets" or self.path=="/sets_driver":
            if form.has_key("save"):
                qs=self.db.tb_sets._upd_post(form)
                for q in qs:
                    self.db.run(q)
                # autosave set d_devtype
                if form.has_key("d_name"):
                    self.create_dtp()
                    if self.dtpclient._get_printer_info(form['d_name'].value):
                        self.db._sets_upd('d_devtype',self.dtpclient.printer_info['type_device'])
                        self.db._sets_upd('d_speed',self.dtpclient.printer_info['speed'])
                    else:
                        self.db._sets_upd('d_devtype','None')
                    if form.has_key("usr_pass") and form.has_key("adm_pass"):
                        self.dtpclient._set_printer_info(form['d_name'].value,"usr_pass",form['usr_pass'].value)
                        self.dtpclient._set_printer_info(form['d_name'].value,"adm_pass",form['adm_pass'].value)
                    del self.dtpclient
                # ----------------------
            self._redirect(self.path)
            return

        if self.path=='/sets/autosets':
            if form.has_key("save"):
                if self.currule<RULE_ADMIN:
                    self._redirect("/")
                    return
                qs=self.db.tb_sets._upd_post(form,'device')
                for q in qs:
                    self.db.run(q)
            self._redirect("/sets")
            return

        if self.path=="/printer/textlines":
            if self.currule<RULE_ADMIN:
                self._redirect("/")
                return
            printer=self.db.sets['d_name']
            self.create_dtp()
            if self.db.sets['d_devtype']=='KKM_FPRINT':
                if not self.dtpclient._cmd_prn_tabgets_CHR(printer):
                    self._writetxt(self.dtpclient.result_name)
                    return
                params=[]
                for i in range(20):
                    n="textline_%d" % i
                    if form.has_key(n):
                        params.append(form[n].value.decode("utf8"))
                self.dtpclient._cmd_prn_tabset(printer,params)
            if self.db.sets['d_devtype']=='KKM_SHTRIHM':
                if not self.dtpclient._cmd_prn_tabget_textlines(printer):
                    self._writetxt(self.dtpclient.result_name)
                    return
                for i in range(20):
                    n="textline_%d" % i
                    if form.has_key(n):
                        self.dtpclient._cmd_prn_tabset_shtrih(printer,i+1,form[n].value.decode("utf8"))
            del self.dtpclient
            self._redirect("/sets_driver")
            return

        """ POST REG REQUEST
            ----------------
        """    

        if self.path=='/reg/pay':
            if not form.has_key("nal") or not form.has_key("bnal"):
                self._writetxt(POST_FALSE)
                return
            nal=form['nal'].value
            bnal=form['bnal'].value
            nal=float(nal)
            bnal=float(bnal)
            printer=self.db.sets["d_name"]

            """-------------------------------------------"""
            self.create_check()
            self.create_dtp()
            self.check._init_dtp(self.dtpclient)
            """-------------------------------------------"""

            if printer=='None':
                ncheck=0
            else:
                if self.dtpclient._cm(printer,"prn_getcheck",{}):
                    ncheck=self.dtpclient.return_data
                    if int(ncheck)==0:
                        ncheck=self.db._trsc_last()+1
                else:
                    ncheck=self.db._trsc_last()+1

            try:
                ice_lock()
                nboxes=self.db._select(db.TB_CHECK_CONT," idcheck=0 and iduser=%s and nbox<>0" % self.iduser,fields=["nbox"],group='nbox',toarr=True)
                f=True
                res=self.check._pay(ncheck,nal,bnal)
                if res and len(nboxes)>0:
                    self.create_icerest()
                    for n in nboxes:
                        r=self.icerest.clear_zakaz(n)
                        f = f and r
                    del self.icerest
            except Exception, ex:
                print ex
                res=False
            finally:
                ice_unlock()
            
            JSON=json.dumps({"error":self.check.error,"sdacha":self.check.sdacha,"prize":self.check.prize},ensure_ascii=False)
            self._writejson(JSON)
            del self.check
            return

        if self.path=='/reg/add_code':
            if not form.has_key("code"):
                self._writetxt(POST_FALSE)
                return
            code=form['code'].value
            if form.has_key("barcode"):
                barcode=form['barcode'].value
            else:
                barcode=None

            self.create_check()
            try:
                ice_lock()
                self.check._load_cur()
                id=self.check._add_tov(code,1,barcode)
            except:
                id=0
            finally:
                ice_unlock()

            if id==0:
                self._writetxt(POST_FALSE)
                return
            if id<0:
                self._writetxt(str(id))
                return
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/add_shcode':
            if not form.has_key("code") or not form.has_key("warning"):
                self._writetxt(POST_FALSE)
                return
            if form.has_key("barcode"):
                barcode=form['barcode'].value
            else:
                barcode=None
            code=form['code'].value
            self.create_check()

            try:
                ice_lock()
                self.check._load_cur()
                self.check.warning=form['warning'].value
                r=self.check._add_shk(code,barcode)
            except:
                r=False
            finally:
                ice_unlock()

            if r<0:
                self._writetxt(str(r))
                return
            if not r:
                self._writetxt(POST_FALSE)
                return
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/set':
            if form.has_key("field") and form.has_key("value"):
                self.create_check()
                if form['field'].value in ['type','bonus_type','bonus_discount']:
                    self.check._load_cur()
                    if self.db.ch_head['ro']!=0:
                        self._writetxt(POST_FALSE)
                        return
                if str(form['value'].value)=='null':
                    form['value'].value=''
                try:
                    ice_lock()
                    self.check._set(form['field'].value,form['value'].value)
                finally:
                    ice_unlock()

                del self.check
                self._writetxt(POST_TRUE)
                return
            self._writetxt(POST_FALSE)
            return

        if self.path=='/reg/printshk':
            if not form.has_key("idpos"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            self.create_dtp()
            self.check._init_dtp(self.dtpclient)
            self.check._print_shk(int(form['idpos'].value))
            del self.check
            del self.dtpclient
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/storno':
            if not form.has_key("idpos"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            try:
                ice_lock()
                self.check._storno(int(form['idpos'].value))
            finally:
                ice_unlock()
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/chcount':
            if not form.has_key("idpos") or not form.has_key("count"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            val=form['count'].value
            val=val.replace(',','.')
            try:
                val=float(val)
            except:
                self._writetxt(POST_FALSE)
                del self.check
                return
            try:
                ice_lock()
                res=self.check._chcount(int(form['idpos'].value),val)
            except:
                res=False
            finally:
                ice_unlock()
            if not res:
                self._writetxt(POST_FALSE)
                del self.check
                return
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/chskid':
            if not form.has_key("idpos") or not form.has_key("proc"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            val=form['proc'].value
            val=val.replace(',','.')
            try:
                val=float(val)
            except:
                self._writetxt(POST_FALSE)
                del self.check
                return
            try:
                ice_lock()
                res=self.check._chskid(int(form['idpos'].value),val)
            except:
                res=False
            finally:
                ice_unlock()
            if not res:
                self._writetxt(POST_FALSE)
                del self.check
                return
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/chprice':
            if not form.has_key("idpos") or not form.has_key("price"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            val=form['price'].value
            val=val.replace(',','.')
            try:
                val=float(val)
            except:
                self._writetxt(POST_FALSE)
                del self.check
                return
            try:
                ice_lock()
                res=self.check._chprice(int(form['idpos'].value),val)
            except:
                res=False
            finally:
                ice_unlock()
            if not res:
                self._writetxt(POST_FALSE)
                del self.check
                return
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/selprice':
            if not form.has_key("idpos"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            if not self.check._selprice(int(form['idpos'].value)):
                self._writetxt(POST_FALSE)
                del self.check
                return
            j=json.dumps(self.db.price_shk,ensure_ascii=False)
            del self.check
            self._writejson(j)
            return

        if self.path=='/reg/setprice':
            if not form.has_key("idpos") or not form.has_key("cena"):
                self._writetxt(POST_FALSE)
                return
            self.create_check()
            try:
                ice_lock()
                res=self.check._setprice(int(form['idpos'].value),form['cena'].value)
            except:
                res=False
            finally:
                ice_unlock()
            if not res:
                self._writetxt(POST_FALSE)
                del self.check
                return
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/cancel':
            printer=self.db.sets["d_name"]
            if printer=='None':
                ncheck=0
            else:
                ncheck=1
            self.create_check()
            try:
                ice_lock()
                nboxes=self.db._select(db.TB_CHECK_CONT," idcheck=0 and iduser=%s and nbox<>0" % self.iduser,fields=["nbox"],group='nbox',toarr=True)
                f=True
                if len(nboxes)>0:
                    self.create_icerest()
                    for n in nboxes:
                        r=self.icerest.unblock_zakaz(n)
                        f = f and r
                    del self.icerest
                if f:
                    self.check._cancel(ncheck)
            finally:
                ice_unlock()
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/savecheck':
            self.create_check()
            try:
                ice_lock()
                self.check._calc()
                id=self.check._save()
            finally:
                ice_unlock()
            del self.check
            self._writetxt(str(id))
            return

        if self.path=='/reg/loadcheck':
            if not form.has_key("id") or not form.has_key("iduser") :
                self._writetxt(POST_FALSE)
                return
            id=int(form['id'].value)
            iduser=int(form['iduser'].value)
            self.create_check()
            try:
                ice_lock()
                res=self.check._loadcheck(iduser,id)
            except:
                res=False
            finally:
                ice_unlock()
            if not res:
                self._writetxt(POST_FALSE)
                del self.check
                return
            del self.check
            self._writetxt(POST_TRUE)
            return

        if self.path=='/reg/loadchecks':
            if self.currule<=RULE_SELLER:
                al=False
            else:
                al=True
            self.create_check()
            if not self.check._loadchecks(al):
                self._writetxt(POST_FALSE)
                del self.check
                return
            j=json.dumps(self.db.checks,ensure_ascii=False)
            del self.check
            self._writejson(j)
            return

        """ POST FILES REQUEST
            ----------------
        """    
        if (self.path.find("/files")==0):
            if self.currule<RULE_ADMIN:
                self._writetxt(POST_FALSE)
                return
            if form.has_key("file"): 
                fn=form['file'].filename
                file_data=form['file'].file.read()
                path=self.path.replace("..","")
                p=path+"/"+fn
                f=os.path.basename(p)
                d=os.path.dirname(p)
                if self.put_file(file_data,path+"/"+fn):
                    self._writetxt(POST_TRUE)
                else:
                    self._writetxt(POST_FALSE)
                del file_data
            else:
                self._writetxt(POST_FALSE)
            return

        """ POST EGAIS
            ----------------
        """    

        if self.path=="/egais/put/doc":
            if not form.has_key("id") or not form.has_key("hd") or not form.has_key("ct"): 
                self.return_false()
                return
            
            id=int(form['id'].value)
            hd=json.loads(form["hd"].value)
            ct=json.loads(form["ct"].value)

            if id!=0:
                doc=self.db._select(db.TB_EGAIS_DOCS_HD,"id=%s" % id)
                if len(doc)==0:
                    self.return_false()
                    return
                doc=doc[0]
                if doc['status']>1:
                    self.return_false()
                    return
                #self.db._delete(TB_EGAIS_DOCS_CT,"iddoc=%s" % id)

            pl_send=self.db._select(db.TB_EGAIS_PLACES,"KPP='%s'" % self.db.sets['kpp'])[0]
            pl_recv=self.db._select(db.TB_EGAIS_PLACES,"ClientRegId='%s'" % hd['recv_RegId'])[0]
            struct={'wb_Identity':hd['wb_NUMBER'],'wb_NUMBER':hd['wb_NUMBER'],'wb_Date':hd['wb_Date'],'wb_ShippingDate':hd['wb_Date'],'wb_Type':hd['wb_Type'],'wb_UnitType':hd['wb_UnitType'],'type':"2",'status':hd['status'],\
            'send_INN':pl_send['INN'],'send_KPP':pl_send['KPP'],'send_ShortName':pl_send['ShortName'],'send_RegId':pl_send['ClientRegId'],'recv_INN':pl_recv['INN'],'recv_KPP':pl_recv['KPP'],'recv_ShortName':pl_recv['ShortName'],'recv_RegId':pl_recv['ClientRegId']}
            if id==0:
                if not self.db._insert(db.TB_EGAIS_DOCS_HD,struct):
                    self.return_false()
                    return
                id=self.db.lastid
            else:
                if not self.db._update(db.TB_EGAIS_DOCS_HD,struct,"id=%s" % id):
                    self.return_false()
                    return

            identity=0
            for d in ct:
                identity+=1
                ost=self.db._select(db.TB_EGAIS_OSTAT,"id='%s'" % d[0])[0]
                struct={'wb_Identity':str(identity),'iddoc':id,\
                'pref_Type':'АП','pref_ShortName':ost['pref_FullName'],'pref_AlcCode':ost['pref_AlcCode'],'pref_AlcVolume':ost['pref_AlcVolume'],'pref_ProductVCode':ost['pref_ProductVCode'],'pref_Capacity':ost['pref_Capacity'],\
                'wbr_InformBRegId':ost['rst_InformBRegId'],'pref_RegId':ost['rst_InformARegId'],\
                'oref_ClientRegId':ost['oref_ClientRegId'],'oref_INN':ost['oref_INN'],'oref_KPP':ost['oref_KPP'],'oref_ShortName':ost['oref_ShortName'],\
                'wb_Quantity':ost['rst_Quantity'],'real_Quantity':d[1],'wb_Price':'0'}
                self.db._insert(db.TB_EGAIS_DOCS_CT,struct)
            self.return_true()
            return

        if self.path=="/egais/put/mydoc":
            if not form.has_key("iddoc"): 
                self.wfile.write(POST_FALSE)
            idd=int(form['iddoc'].value)
            status=int(form['status'].value)
            answer=form['answer'].value

            if not self.db.egais_get_mydoc(idd):
                self.wfile.write(POST_FALSE)
                return
            if int(self.db.egais_doc_hd['status'])>1:
                self.wfile.write(POST_FALSE)
                return
            if self.db.egais_docs_hd_upd(idd,{'status':status,'answer':answer}):
                self.wfile.write(POST_TRUE)
            else:
                self.wfile.write(POST_FALSE)
            return

        if self.path=="/egais/del/mydoc":
            if not form.has_key("iddoc"): 
                self.wfile.write(POST_FALSE)
            idd=int(form['iddoc'].value)
            if not self.db.egais_get_mydoc(idd):
                self.wfile.write(POST_FALSE)
                return
            if int(self.db.egais_doc_hd['status'])>1:
                self.wfile.write(POST_FALSE)
                return
            if self.db.egais_docs_del(idd):
                self.wfile.write(POST_TRUE)
            else:
                self.wfile.write(POST_FALSE)
            return

        if self.path=="/egais/put/position":
            if not form.has_key("iddoc") or not form.has_key("identity"): 
                self.wfile.write(POST_FALSE)
            idd=int(form['iddoc'].value)
            id=int(form['identity'].value)
            quantity=form['quantity'].value

            if not self.db.egais_docs_ct_getpos(idd,id):
                self.wfile.write(POST_FALSE)
                return
            if float(quantity) > float(self.db.egais_doc_ct['wb_Quantity']):
                self.wfile.write(POST_FALSE)
                return
            if self.db.egais_docs_ct_upd(idd,id,{'real_Quantity':quantity}):
                self.wfile.write(POST_TRUE)
            else:
                self.wfile.write(POST_FALSE)
            return

        """ POST DTP REQUEST
            ----------------
        """    

        if self.path=="/cmd_autocreate":
            if self.currule<=RULE_SELLER:
                self._redirect("/")
                return
            self.create_dtp()
            if self.dtpclient._cmd_autocreate("KKM_FPRINT"):
                self.wfile.write(POST_TRUE)
            else:
                self.wfile.write(POST_FALSE)
            del self.dtpclient
            return

        if self.path=="/cmd/prn_setcurdatetime":
            if self.currule<RULE_ADMIN:
                self._redirect("/")
                return
            if not self.db.sets['d_devtype'] in ('KKM_FPRINT','KKM_SHTRIHM'):
                self.wfile.write(CMD_ERROR)
                return
            printer=self.db.sets['d_name']
            self.create_dtp()
            self.dtpclient._cmd_prn_setcurdatetime(printer)
            self._writetxt(self.dtpclient.result_name)
            del self.dtpclient
            return


        self.send_response(200)
        self.end_headers()

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Создаем веб сервер многопоточный """

if __name__ == '__main__':
    dbase = db.dbIceCash(db.DATABASE, MYSQL_HOST, db.MYSQL_USER, db.MYSQL_PASSWORD) 
    if dbase.open():
        dbase._tables()
        dbase._recreate()
        pass
    else:
        print "DTPWeb Server down. Database not exist"
        sys.exit(1)

    dbase._read_sets()
    if not 'nofiscal_proc' in dbase.sets:
        dbase._sets_add('magazine','nofiscal_proc','0')
    print "opened database"
    #ice_create_lock()

    server = ThreadedHTTPServer(('', int(dbase.sets['server_port'])), Handler)
    
    print 'Start dIceCash Server v %s [%s]' % (VERSION,dbase.sets['server_port'])
    dbase.close()

    if dbase.sets['dev_scanner']!='None' and dbase.sets['dev_scanner']!='':
        startservice("su kassir -c \"python serialtokbd.py %s\"" % dbase.sets['dev_scanner'])
        print "start service rs232 scanner"

    #startservice("python dUpload.py start_upload")
    #print "start service upload"
    server.serve_forever()


