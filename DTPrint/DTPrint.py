#!/usr/bin/python
# -*- coding: utf-8

"""
    Web Driver Thermo Printers and Fprint KKM
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
    2017-04-09
"""

import xml.etree.ElementTree as etree
import printer
import fprint
import shtrihm
from lsusb import lsserial,lsusb,lsdir
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from SocketServer import ThreadingMixIn
import threading
import urlparse
import cgi
import Cookie
import time
import sys,os
from md5 import md5
import json

import dbDTPrint

VERSION="1.0.030"
MAX_PRINTERS = 16
CMD_SHTRIHM = [\
        "_beep",\
        "prn_devstatus",\
]
CMD_FPRINT = [\
        "_beep",\
        "prn_devstatus",\
        "prn_sound_dartweider",\
]
CMD_ESCPOS = [\
        "print_text",\
        "print_barcode",\
        "print_qrcode",\
        "print_image",\
        "set_style",\
        "cut",\
        "cashdraw",\
        "sensors",\
]
    
    


prlocks=[]
def create_prlocks ():
    for i in range(MAX_PRINTERS):
        prlocks.append(threading.Lock())

def lock_printer(id):
    prlocks[id].acquire()

def unlock_printer(id):
    prlocks[id].release()

def rep_empty(v,default):
    if v=="":
        return default
    else:
        return v

def hash2xml(h):
    r=""
    for k,v in h.items():
        #if type(v)==str:
        #    v=v.encode("utf8")
        r+="<%s>%s</%s>\n" % (k,v,k)
    return r

def arr2xml(tag,a):
    r=""
    for v in range(len(a)):
        #if type(a[v])==str:
        #    a[v]=a[v].encode("utf8")
        r+=u"<%s id=\"%d\">%s</%s>\n" % (tag,v,a[v],tag)
    return r
    #.encode("utf8")

def hash2htmtable(h,n,on=""):
    keys=h.keys()
    keys.sort()
    l=len(keys)
    l1=l//n
    if (l%n)>0:
        l1+=1
    r=""
    for j in range(l1):
        r+="<tr>"
        for i in range(n):
            x=j*n+i
            if x>=l:
                break
            k=keys[x]
            v=h[k]
            if (v==False)or(v==True):
                c='red'
            else:
                c=''
            r+="<td class='green small'>%s</td><td id='%s' %s class='%s small'>%s</td>" % (k,k,on,c,v)
        r+="</tr>\n"
    return r

def arr2htmtable(id,a,on=""):
    r=""
    i=0
    for v in a:
        r+="<tr>"
        _on=on.replace("%id%",str(i))
        r+="<td class='green small' %s id='%s' >%s</td>" % (_on,id,v.encode('utf8'))
        r+="</tr>\n"
        i+=1
    return r

class Handler(BaseHTTPRequestHandler):

    def mysql_open(self):
        self.db = dbDTPrint.dbDTPrint(dbDTPrint.DATABASE, 'localhost', dbDTPrint.MYSQL_USER, dbDTPrint.MYSQL_PASSWORD)
        return self.db.open()
        
    def _do_HEAD(self,tp,code=200):
        self.send_response(code)
        self.send_header("Content-type", tp)
        self.end_headers()

    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", 'text/html')
        self.end_headers()

    def _send_HEAD(self,tp,code=200):
        self.send_response(code)
        self.send_header("Content-type", tp)
        self.end_headers()

    def _writetxt(self,html,encode=True):
        self._send_HEAD("text/html")
        if encode:
            self.wfile.write(html.encode("utf8"))
        else:
            self.wfile.write(html)


    def _writejson(self,j):
        self._send_HEAD("application/json")
        self.wfile.write(j.encode("utf8"))

    def ReadCookie(self):
        if "Cookie" in self.headers:
            c = Cookie.SimpleCookie(self.headers["Cookie"])
            if c.has_key('login'):
                return c['login'].value
            else:
                return None

    def WriteCookie(self,form):
        if form.has_key("login"):
            c = Cookie.SimpleCookie()
            c['login'] = form["login"].value
            self.send_header('Set-Cookie', c.output(header=''))
        else:
            self.wfile.write("No LOGIN!")
    
    def Redirect(self,url):
        self.send_response(302)
        self.send_header('Location', url)

    def write_pattern(self,p,amark,aval):
        html=self.get_file(p)
        for i in range(len(amark)):
            html=html.replace(amark[i],aval[i])
        return html

    def write_pattern_hash(self,p,h):
        html=self.get_file(p)
        for key,val in h.items():
            k="%"+key+"%"
            if type(val) == unicode:
                v = val.encode('utf8')
            else:
                v=str(val)
            html=html.replace(k,v)
        return html

    def write_body(self,b):
        self._do_HEAD("text/html")
        html=self.get_file('/index.html')
        info='%s %s' % (self.user,self.client_address[0])
        html=html.replace("%version%",VERSION)
        html=html.replace("%info%",info)
        html=html.replace("%body%",b)
        self.wfile.write(html)
    
    def write_file(self,f):
        self._do_HEAD("application/x")
        html=self.get_file(f)
        self.wfile.write(html)

    def get_file(self,path):
        if path[0]!='/':
            path='/'+path
        path='site'+path
        try:
            f=open(path,"r")
            message=f.read()
            f.close()
        except:
            message=''
            print path
            pass
        return message

    def put_file(self,filedata,path):
        path='site'+path
        try:
            f=open(path,"w")
            f.write(filedata)
            f.close()
        except:
            print path
            pass
        return 

    def verify(self,login):   
        if self.db.sets['password_usr']==md5(login).hexdigest():
            self.user='usr'
        elif self.db.sets['password_adm']==md5(login).hexdigest():
            self.user='adm'
        else:
            return False
        return True

    def html_arrstr2select(self,arr,val):
        s=""
        for i in range(len(arr)):
            if arr[i]==val:
                ch='selected'
            else:
                ch=""
            s+="<option value='%s' %s >%s</option>\n" % (arr[i],ch,arr[i][:40])
        return s

    def html_arr2select(self,arr,val):
        s=""
        for i in range(len(arr)):
            if i==val:
                ch='selected'
            else:
                ch=""
            s+="<option value=%d %s >%s</option>\n" % (i,ch,arr[i])
        return s
    
    def html_db2select(self,records,field_id,field_val,val):
        s=""
        for record in records:
            if record[field_id]==val:
                ch='selected'
            else:
                ch=""
            s+="<option value='%s' %s >%s</option>\n" % (str(record[field_id]),ch,str(record[field_val]))
        return s


    def create_printer(self,prn):
        try:
            if dbDTPrint.TYPE_DEVICE[prn['type_device']].find('ESCPOS')!=-1:
                if dbDTPrint.TYPE_CONNECT[prn['type_connect']]=='SERIAL':
                    #print "create printer serial device:%s" % prn['device']
                    self.ep=printer.Serial(prn['device'])
                if dbDTPrint.TYPE_CONNECT[prn['type_connect']]=='USB':
                    id_vendor=int('0x'+prn['id_vendor'],16)
                    id_product=int('0x'+prn['id_product'],16)
                    byte1=int(prn['byte1'],16)
                    byte2=int(prn['byte2'],16)
                    #print "create printer usb device:%s:%s,%d;%s,%s" % (hex(id_vendor),hex(id_product),prn['interface'],hex(byte1),hex(byte2))
                    self.ep=printer.Usb(id_vendor,id_product,prn['interface'],in_ep=byte1, out_ep=byte2)
                if dbDTPrint.TYPE_CONNECT[prn['type_connect']]=='NET':
                    #print "create printer network:%s:%d" % (prn['address'],prn['port'])
                    self.ep=printer.Network(prn['address'], port=prn['port'])
                    return True
                if self.ep.device is None:
                    print "error create printer"
                    return False
                else:
                    return True
            if dbDTPrint.TYPE_DEVICE[prn['type_device']]=="KKM_FPRINT":
                if dbDTPrint.TYPE_CONNECT[prn['type_connect']]=='NET':
                    ip=prn['address']
                    port=prn['port']
                else:
                    ip=""
                    port=prn['device']
                #print "create fprint serial device:%s" % prn['device']
                self.ep=fprint.KKM_FPRINT(  echo=False,ip=ip,port=port,speed=prn['speed'],\
                                            password=fprint.BCD2data(prn['usr_pass']),\
                                            admpassword=fprint.BCD2data(prn['adm_pass']))
                return True

            if dbDTPrint.TYPE_DEVICE[prn['type_device']]=="KKM_SHTRIHM":
                #print "create shtrihm serial device:%s" % prn['device']
                self.ep=shtrihm.frk(port=prn['device'],speed=prn['speed'])
                return True
        except:
            return False

    def _do_print_escpos(self,prn,cm_command,cm_param,xmlformat=True):
        """ PRINT ONLY THERMAL PRINTER ESCPOS"""
        try:
            xml_params=etree.fromstring(cm_param)
        except:
            xml_params=None
        params={}
        #print "ESCPOS:%s" % cm_command
        if xml_params!=None and xml_params.tag=='list':
            plist=xml_params
            params={}
            for line in plist:
                pname=line.find('n')
                pvalue=line.find('v')
                
                param_type="value"
                if len(line.items())!=0:
                    if line.items()[0][0]=='type':
                        param_type=line.items()[0][1]
                if param_type=='value':
                    if pvalue.text==None:
                        tx=''
                    else:
                        tx=pvalue.text
                    params[pname.text]=tx
                if param_type=='array':
                    ps=[]
                    for subv in pvalue:
                        if subv.text==None:
                            tx=''
                        else:
                            tx=subv.text
                        ps.append(tx)
                    params[pname.text]=ps
            
        #print params
        return_data=""
        return_type="text"
        return_id=-1

        self.ep.set(codepage=prn['charset_driver'],code=prn['charset_device'])
        if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='ESCPOS_OLD':
            self.ep._set_oldstyle_command(True)
        else:
            self.ep._set_oldstyle_command(False)

        if cm_command=='set_style':
            _bold=False
            _invert=False
            astyle=params['adata']
            if len(astyle)==0:
                _size='normal'
            else:
                _size=''
            _align='left'
            _font='a'
            try:
                if astyle[0]=='bold':
                    _bold=True
                if astyle[1]!='':
                    _size=astyle[1]
                if astyle[2]!='':
                    _font=astyle[2]
                if astyle[3]!='':
                    _align=astyle[3]
                if astyle[4]!='':
                    _invert=True
                return_id=0
            except:
                return_id=101
            self.ep.set(bold=_bold,size=_size,font=_font,align=_align,inverted=_invert)

        if cm_command=='print_barcode':
            asets=params['adata']
            try:
                asets[0]=rep_empty(asets[0],"EAN13")
                asets[1]=rep_empty(asets[1],"64")
                asets[2]=rep_empty(asets[2],"3")
                asets[3]=rep_empty(asets[3],"None")
                asets[4]=rep_empty(asets[4],"BELOW")
                self.ep.barcode(bc=asets[0],width=int(asets[1]),height=int(asets[2]),code=asets[3],pos=asets[4],font="")
                return_id=0
            except:
                return_id=self.ep.resultcode

        if cm_command=='print_image':
            try:
                self.ep.image('site/files/'+params['filename'])
                return_id=0
            except:
                return_id=self.ep.resultcode

        if cm_command=='print_qrcode':
            try:
                self.ep.qr(params['text'],int(params['size']))
                return_id=0
            except:
                return_id=self.ep.resultcode

        if cm_command=='print_text':
            try:
                self.ep.text(params['text']+"\n")
                return_id=0
            except:
                return_id=self.ep.resultcode

        if cm_command=='cut':
            self.ep.cut()

        if cm_command=='cashdraw':
            try:
                self.ep.cashdraw(int(params['pin']))
                return_id=0
            except:
                return_id=self.ep.resultcode

        if cm_command=='sensors':
            s1 = self.ep.is_error()
            return_id=0
            return_data = '<sens_error>%s</sens_error>' % s1

        self.ep.MAX_WIDTH=prn['width']
        self.ep.MAX_PIXEL_WIDTH=prn['dpi']

        """ --------------- COMMANDS ------------------------ """

        sensor = False
        #sensor=self.ep.is_error()
        if cm_command == "prn_devstatus":
            self.ep.DEVICE={
                'dev_id'    :'none',\
                'dev_name'  :'escpos',\
                'dev_wchar' :48,\
                'dev_pix'   :384,\
                'c_check'   :0,\
                'fc_notpaper' :sensor\
            }
           # print self.ep.DEVICE
            return_type="hash"
            return_id=0
            if not self.ep._iserror():
                if xmlformat:
                    return_data=hash2xml(self.ep.DEVICE)

        else:
            if sensor:
                return_id=1
                return self.result_xml(return_id,return_data,return_type)

        if cm_command == "_beep":
            self.ep.beep()

        if cm_command == "prn_sound_dartweider":
            self.ep.beep()
            self.ep.beep()
            self.ep.beep()

        if cm_command == "_register":
            pass

        if cm_command == "_return":
            pass

        if cm_command == "_reportX":
            pass

        if cm_command == "_reportZ":
            pass

        if cm_command == "_openbox":
            self.ep.cashdraw(2)
            self.ep.cashdraw(5)

        if cm_command == "_cut":
            if int(params['type'])==0:
                t='PART'
            else:
                t='FULL'
            self.ep.cut(t)

        if cm_command == "_roll":
            self.ep.prn_roll(int(params['count']))

        if cm_command == "_printsh":
            pass

        if cm_command == "_printcode":
            self.ep.barcode(params['text'],'EAN13',int(params['width']),6,'BELOW','b')

        if cm_command == "_opencheck":
            pass

        if cm_command == "_cancelcheck":
            pass

        if cm_command == "_discount":
            pass

        if cm_command == "_closecheck":
            pass

        if cm_command == "prn_line":
            self.ep.prn_line(params['ch'])

        if cm_command == "prn_lines":
            if params.has_key('bright'):
                _bright=int(params['bright'])
            else:
                _bright=0
            if params.has_key('align'):
                _align=params['align']
            else:
                _align='left'
            if params.has_key('invert'):
                _invert=bool(int(params['invert']))
            else:
                _invert=False
            self.ep.prn_lines(text=params['text'],\
            big=bool(int(params['big'])),font=int(params['font']),height=int(params['height']),bright=_bright,invert=_invert,align=_align)

        if cm_command == "prn_lines_def":
            self.ep.prn_lines(text=params['text'])

        if cm_command == "prn_sale_style":
            if params.has_key('bold'):
                _bold=bool(int(params['bold']))
            else:
                _bold=False
            self.ep.prn_sale_style(text=params['text'],val=params['value'],ch=params['ch'],bold=_bold)

        if cm_command == "prn_sale_short":
            self.ep.prn_sale_short(\
            params['oper'],\
            params['section'],\
            params['p1'],params['p2'],params['p3'],\
            params['ch'],params['bonus'],params['discount'],params['line'])

        if cm_command == "prn_sale_itog":
            self.ep.prn_sale_itog(vsego=params['vsego'],\
            discount=params['discount'],itogo=params['itogo'],nal=params['nal'],bnal=params['bnal'],sdacha=params['sdacha'],ch=params['ch'])

        if cm_command == "prn_head":
            self.ep.prn_sale_head(params['ncheck'],params['dt'],params['tm'])

        if cm_command == "prn_image":
            self.ep.image('site/files/'+params['path'])

        if cm_command == "prn_qr":
            self.ep.qr(params['text'],5)

        if cm_command == "prn_getcheck":
            return_data="0"

        if return_id==-1:
            return_id=self.ep.resultcode
            #print "resultcode=%s" % hex(return_id)
        if xmlformat:
            return self.result_xml(return_id,return_data,return_type)
        else:
            return return_id

    def _do_print_kkm_fprint(self,prn="",cm_command="",cm_param="",xmlformat=True):
        """ PRINT KKM FPRINT """
        try:
            xml_params=etree.fromstring(cm_param)
        except:
            xml_params=None
        params={}
        #print "FPRINT:%s" % cm_command
        #print "PARAMS:%s" % cm_param
        if xml_params!=None and xml_params.tag=='list':
            plist=xml_params
            params={}
            for line in plist:
                pname=line.find('n')
                pvalue=line.find('v')
                
                param_type="value"
                if len(line.items())!=0:
                    if line.items()[0][0]=='type':
                        param_type=line.items()[0][1]
                if param_type=='value':
                    if pvalue.text==None:
                        tx=''
                    else:
                        tx=pvalue.text
                    params[pname.text]=tx
                if param_type=='array':
                    ps=[]
                    for subv in pvalue:
                        if subv.text==None:
                            tx=''
                        else:
                            tx=subv.text
                        ps.append(tx)
                    params[pname.text]=ps
            
       # print "params",params
        return_data=""
        return_type="text"
        return_id=-1
        """ --------------- CONNECT ------------------------- """
        if not self.ep.connect():
            return_data = "<comment>not connect</comment>"
            return_id = 4

        self.ep.MAX_WIDTH=prn['width']
        self.ep.MAX_PIXEL_WIDTH=prn['dpi']

        """ --------------- COMMANDS ------------------------ """
        if cm_command == "prn_devstatus":
            self.ep.prn_devstatus()
            return_type="hash"
            if not self.ep._iserror():
                if xmlformat:
                    return_data=hash2xml(self.ep.DEVICE)
                self.db.run(self.db.tb_printers._upd(prn['name'],\
                    {'dpi':self.ep.DEVICE['dev_wpix'],\
                     'width':self.ep.DEVICE['dev_wchar'],\
                     'vendor':self.ep.DEVICE['dev_name']\
                    }))

        if cm_command == "prn_tabgets_BCD":
            values=self.ep.prn_tabgets_BCD()
            return_type="hash"
            if not self.ep._iserror():
                if xmlformat:
                    return_data=hash2xml(values)

        if cm_command == "prn_tabgets_CHR":
            return_type="array"
            self.ep.prn_tabgets_CHR(tabval=params['tabval'],\
                                        incrow=int(params["incrow"]),\
                                        nvalues=int(params['nvalues']))
            if not self.ep._iserror():
                if xmlformat:
                    return_data=arr2xml(params['tabval'],self.ep.tabvalues)

        if cm_command == "prn_tabset":
            if self.ep._setmode_prog():
                self.ep.prn_tabset( tabval=params['tabval'],\
                                incrow=int(params["incrow"]),\
                                value=params['value'],
                                nvalues=int(params['nvalues']))
            if not self.ep._iserror():
                self.ep._exitmode()
                if xmlformat:
                    return_data="setting accept"

        if cm_command == "prn_setcurtime":
            self.ep.prn_setcurtime()

        if cm_command == "prn_setcurdate":
            self.ep.prn_setcurdate()

        if cm_command == "_beep":
            self.ep._beep()

        if cm_command == "prn_sound_dartweider":
            self.ep.prn_sound_dartweider()

        if cm_command == "_register":
            self.ep._register(params['p1'],params['p2'],params['section'])

        if cm_command == "_register":
            self.ep._register(params['p1'],params['p2'],params['section'])

        if cm_command == "_registerpos":
            self.ep._registerpos(params['title'],params['p1'],params['p2'],params['tdiscount'],params['znak'],params['size'],params['nalog'],params['section'])

        if cm_command == "_returnpos":
            self.ep._returnpos(params['title'],params['p1'],params['p2'],params['tdiscount'],params['znak'],params['size'],params['nalog'],params['section'])

        if cm_command == "_return":
            self.ep._return(params['p1'],params['p2'])

        if cm_command == "_incash":
            self.ep._incash(params['summa'])

        if cm_command == "_outcash":
            self.ep._incash(params['summa'])

        if cm_command == "_reportX":
            self.ep._reportX(int(params['type']))

        if cm_command == "_reportZ":
            self.ep._reportZ()

        if cm_command == "_openbox":
            self.ep._openbox()

        if cm_command == "_opensmena":
            self.ep._opensmena()

        if cm_command == "_preitog":
            pass

        if cm_command == "_renull":
            self.ep._renull()

        if cm_command == "_cut":
            self.ep._cut(bool(int(params['type'])))

        if cm_command == "_roll":
            self.ep.prn_roll(int(params['count']))

        if cm_command == "_printsh":
            self.ep._printsh()

        if cm_command == "_printcode":
            self.ep._printcode(t=int(params['type']),align=int(params['align']),width=int(params['width']),text=params['text'])

        if cm_command == "_opencheck":
            self.ep._opencheck(params['type'])

        if cm_command == "_cancelcheck":
            self.ep._cancelcheck()

        if cm_command == "_discount":
            self.ep._discount(\
            int(params['islast']),\
            int(params['issum']),\
            int(params['isgrow']),\
            params['summa'])

        if cm_command == "_closecheck":
            self.ep._closecheck(int(params['type']),params['summa'])

        if cm_command == "prn_line":
            self.ep.prn_line(params['ch'])

        if cm_command == "prn_lines":
            if params.has_key('align'):
                _align=params['align']
            else:
                _align='left'
            self.ep.prn_lines(text=params['text'],\
            width=int(params['width']),big=bool(int(params['big'])),font=int(params['font']),height=int(params['height']),bright=int(params['bright']),align=_align)

        if cm_command == "prn_lines_def":
            self.ep.prn_lines(text=params['text'])

        if cm_command == "prn_sale_style":
            self.ep.prn_sale_style(text=params['text'],val=params['value'],ch=params['ch'])

        if cm_command == "prn_sale_short":
            self.ep.prn_sale_short(\
            int(params['fiscal']),\
            params['title'],\
            params['oper'],\
            params['section'],\
            params['realcena'],\
            params['p1'],params['p2'],params['p3'],\
            params['ch'],params['bonus'],params['discount'],params['line'],bool(int(params['ofd'])))

        if cm_command == "prn_sale_itog":
            self.ep.prn_sale_itog(vsego=params['vsego'],\
            discount=params['discount'],itogo=params['itogo'],nal=params['nal'],bnal=params['bnal'],sdacha=params['sdacha'],ch=params['ch'])

        if cm_command == "prn_head":
            self.ep.prn_sale_head(params['ncheck'],params['dt'],params['tm'])

        if cm_command == "prn_image":
            self.ep.prn_image(path_img=params['path'],retry=int(params['retry']),margin=int(params['margin']))

        if cm_command == "prn_qr":
            self.ep.prn_qr(params['text'])

        if cm_command == "prn_getcheck":
            #return_data=str(self.ep.prn_getcheck())
            return_data="0"
            self.ep.error=1

        if return_id!=101:
            self.ep.disconnect()

        if return_id==-1:
            return_id=self.ep.error
            print "resultcode=%s" % hex(return_id)

        if xmlformat:
            return self.result_xml(return_id,return_data,return_type)
        else:
            return return_id

    def _do_print_kkm_shtrihm(self,prn="",cm_command="",cm_param="",xmlformat=True):
        """ PRINT KKM SHTRIHM """
        try:
            xml_params=etree.fromstring(cm_param)
        except:
            xml_params=None
        params={}
        #print "SHTRIHM:%s" % cm_command,cm_param
        #print "SHTRIHM:%s" % cm_command
        if xml_params!=None and xml_params.tag=='list':
            plist=xml_params
            params={}
            for line in plist:
                pname=line.find('n')
                pvalue=line.find('v')
                
                param_type="value"
                if len(line.items())!=0:
                    if line.items()[0][0]=='type':
                        param_type=line.items()[0][1]
                if param_type=='value':
                    if pvalue.text==None:
                        tx=''
                    else:
                        tx=pvalue.text
                    params[pname.text]=tx
                if param_type=='array':
                    ps=[]
                    for subv in pvalue:
                        if subv.text==None:
                            tx=''
                        else:
                            tx=subv.text
                        ps.append(tx)
                    params[pname.text]=ps
            
        #print params
        return_data=""
        return_type="text"
        return_id=-1

        """ --------------- CONNECT ------------------------- """
        self.ep.MAX_WIDTH=prn['width']
        self.ep.MAX_PIXEL_WIDTH=prn['dpi']
        if not self.ep.connect():
            return_data = "<comment>not connect</comment>"
            return_id = 4

        """ --------------- COMMANDS ------------------------ """
        if cm_command == "prn_devstatus":
            self.ep.prn_devstatus()
            return_type="hash"
            if not self.ep._iserror():
                if xmlformat:
                    return_data=hash2xml(self.ep.DEVICE)

        if cm_command == "prn_get_tables":
            print "TableStruct" 
            self.TablesStruct=[]
            for i in range(15):
                self.ep.tableStruct(i+1)
                if not self.ep._iserror():
                    self.TablesStruct.append(self.ep.TableStruct)
            return_type="array"
            return_id=0
            if not self.ep._iserror():
                if xmlformat:
                    return_data=arr2xml('tables',self.TablesStruct)

        if cm_command == "prn_get_tabvalues":
            #print "TableValues", params['table'] 
            self.TablesValues=[]
            table=int(params['table'])
            self.ep.tableStruct(table)
            #print self.ep.TableStruct
            for i in range(self.ep.TableStruct[0]):
                fields=[]
                for j in range(self.ep.TableStruct[1]):
                    try:
                        self.ep.fieldStruct(table,i+1,j+1)
                        fields.append(self.ep.FieldStruct)
                    except:
                        pass
                self.TablesValues.append(fields)
            return_type="array"
            return_id=0
            #print 'VALUES', self.TablesValues
            if not self.ep._iserror():
                if xmlformat:
                    textlines=[]
                    for i in range(len(self.TablesValues)):
                        textlines.append(self.TablesValues[i][0][5].decode("utf8"))
                    return_data=arr2xml('values',textlines)


        if cm_command == "prn_tabset":
            print "setTableValue" 
            self.TablesValues=[]
            self.ep.setTableValue(int(params['table']),\
                                int(params["row"]),\
                                int(params["col"]),\
                                params['value'],
                                )
            if not self.ep._iserror():
                if xmlformat:
                    return_data="setting accept"

        if cm_command == "prn_setcurtime":
            self.ep.prn_setcurtime()

        if cm_command == "prn_setcurdate":
            self.ep.prn_setcurdate()
            self.ep.prn_acceptdate()

        if cm_command == "_beep":
            self.ep._beep()

        if cm_command == "prn_sound_dartweider":
            self.ep._beep()
            return_id=0

        if cm_command == "_register":
            self.ep._register(params['p1'],params['p2'],params['section'])

        if cm_command == "_return":
            self.ep._return(params['p1'],params['p2'])

        if cm_command == "_incash":
            self.ep._incash(params['summa'])

        if cm_command == "_outcash":
            self.ep._incash(params['summa'])

        if cm_command == "_reportX":
            self.ep._reportX()

        if cm_command == "_reportZ":
            self.ep._beep()
            self.ep._reportZ()

        if cm_command == "_openbox":
            self.ep._openbox()

        if cm_command == "_opensmena":
            self.ep._opensmena()

        if cm_command == "_preitog":
            self.ep._preitog()

        if cm_command == "_renull":
            self.ep._renull()

        if cm_command == "_setport":
            speeds={2400:0,4800:1,9600:2,19200:3,38400:4,57600:5,115200:6}
            speed=speeds[int(params['speed'])]
            self.ep.setPort(0,speed,156)

        if cm_command == "_cut":
            self.ep._cut(int(params['type']))

        if cm_command == "_roll":
            self.ep._roll(int(params['count']))

        if cm_command == "_printsh":
            self.ep._printsh()

        if cm_command == "_printcode":
            self.ep._printcode(params['text'])

        if cm_command == "_opencheck":
            self.ep._opencheck(params['type'])

        if cm_command == "_cancelcheck":
            self.ep._cancelcheck()

        if cm_command == "_continueprint":
            self.ep.continuePrint()

        if cm_command == "_discount":
            self.ep._discount(\
            int(params['islast']),\
            int(params['issum']),\
            int(params['isgrow']),\
            params['summa'])

        if cm_command == "_closecheck":
            self.ep._closecheck(params['nal'],params['bnal'])

        if cm_command == "prn_line":
            self.ep.prn_line(params['ch'])

        if cm_command == "prn_lines":
            if params.has_key('align'):
                _align=params['align']
            else:
                _align='left'
            self.ep.prn_lines(text=params['text'],\
            big=int(params['big']),height=int(params['height']),\
            width=int(params['width']),font=int(params['font']),align=_align)

        if cm_command == "prn_lines_def":
            self.ep.prn_lines(text=params['text'])

        if cm_command == "prn_sale_style":
            self.ep.prn_sale_style(text=params['text'],val=params['value'],ch=params['ch'])

        if cm_command == "prn_sale_short":
            self.ep.prn_sale_short(\
            int(params['fiscal']),\
            params['title'],\
            params['oper'],\
            params['section'],\
            params['realcena'],\
            params['p1'],params['p2'],params['p3'],\
            params['ch'],params['bonus'],params['discount'],params['line'],bool(int(params['ofd'])))

        if cm_command == "prn_sale_itog":
            self.ep.prn_sale_itog(vsego=params['vsego'],\
            discount=params['discount'],itogo=params['itogo'],nal=params['nal'],bnal=params['bnal'],sdacha=params['sdacha'],ch=params['ch'])

        if cm_command == "prn_head":
            self.ep.prn_sale_head(params['ncheck'],params['dt'],params['tm'])

        if cm_command == "prn_image":
            self.ep.prn_image(path_img=params['path'])

        if cm_command == "prn_qr":
            self.ep.prn_qr(params['text'])

        if cm_command == "prn_getcheck":
            #return_data=str(self.ep.prn_getcheck())
            return_data="0"
            self.ep.error=1

        if return_id!=101:
            self.ep.disconnect()

        if return_id==-1:
            return_id=self.ep.error
            print "SHTRIHM:%s" % cm_command
            print "resultcode=%s" % hex(return_id)

        if xmlformat:
            #print return_data
            return self.result_xml(return_id,return_data,return_type)
        else:
            return return_id

    def do_print_def(self,prn,cm_command,cm_param,xmlformat=True):
        r=""
        self.errcode=0
        if dbDTPrint.TYPE_DEVICE[prn['type_device']].find('ESCPOS')!=-1:
            r=self._do_print_escpos(prn,cm_command,cm_param,xmlformat=xmlformat)
        
        if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_FPRINT':
            r=self._do_print_kkm_fprint(prn=prn,cm_command=cm_command,cm_param=cm_param,xmlformat=xmlformat)
        
        if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_SHTRIHM':
            r=self._do_print_kkm_shtrihm(prn=prn,cm_command=cm_command,cm_param=cm_param,xmlformat=xmlformat)
        return r

    def do_print(self,prn,cm_command,cm_param):
        r=""
        self.errcode=0
        if dbDTPrint.TYPE_DEVICE[prn['type_device']].find('ESCPOS')!=-1:
            r=self._do_print_escpos(prn,cm_command,cm_param,xmlformat=True)
        
        if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_FPRINT':
            r=self._do_print_kkm_fprint(prn=prn,cm_command=cm_command,cm_param=cm_param,xmlformat=True)
        
        if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_SHTRIHM':
            r=self._do_print_kkm_shtrihm(prn=prn,cm_command=cm_command,cm_param=cm_param,xmlformat=True)
        return r

    def do_GET(self):
        parsed_path = urlparse.urlparse(self.path)
        getvals=parsed_path.query.split('&')
        get_vals={}
        for s in getvals:
            if s.find('=')!=-1:
                (key,val) = s.split('=')
                get_vals[key] = val
        self.user=""
        if self.path.find('/cmd')==-1:
            if self.path.find(".html")!=-1:
                self._do_HEAD("text/html",404)
                return
            if self.path.find(".woff")!=-1:
                self._do_HEAD("application/x-font-woff",200)
                message=self.get_file(self.path)
                self.wfile.write(message)
                return
            if self.path.find(".js")!=-1:
                self._do_HEAD("text/javascript",200)
                message=self.get_file(self.path)
                self.wfile.write(message)
                return
            if self.path.find(".css")!=-1:
                self._do_HEAD("text/css",200)
                message=self.get_file(self.path)
                self.wfile.write(message)
                return

            if self.path=='/login':
                self.write_body(self.get_file("/login.html"))
                return

            login=self.ReadCookie()
            if login is None:
                self.Redirect("/login")
                self.end_headers()
                return

            if not self.mysql_open():
                self._do_HEAD("text/html",404)
                return
            else:
                self.db._read_sets()

            if not self.verify(login):
                self.Redirect("/login")
                self.end_headers()
                return

            if self.path=='/sets':
                if self.user!='adm':
                    self.Redirect("/")
                    self.end_headers()
                    return
                b=self.write_pattern("/sets.html",['%addr%','%port%'],\
                [self.db.sets['server_ip'].encode('utf8'),self.db.sets['server_port'].encode('utf8')])
                self.write_body(b)
                return

            if self.path=='/print':
                qresult=self.db.get(self.db.tb_printers._get_names())
                select_printer=self.html_db2select(qresult,0,0,'')
                files=lsdir("site/files")
                select_files=self.html_arrstr2select(files,"")
                x=""
                i=0
                for v in CMD_ESCPOS:
                    i+=1
                    x+="<option value='%d'>%s</option>\n" % (i,v)
                b=self.write_pattern("/print.html",['%printers%','%images%','%cmd_list'],\
                [select_printer,select_files,x])
                self.write_body(b)
                return

            if self.path=='/files':
                files=lsdir('site/files')
                html=""
                for k in files:
                    trash='<span class="glyphicon glyphicon-trash" aria-hidden="true">'
                    fname=k.decode("utf8")
                    html+="<tr><td onclick='window.location=\"/files/%s\"'>%s</td><td onclick='delete_file(\"%s\");''>%s</td></tr>" % (fname,fname,fname,trash)
                    """html+="<tr><td>%s</td><td onclick='delete_file(\"%s\");''>%s</td></tr>" % (fname,fname,trash)"""
                b=self.write_pattern("/files.html",['%files%'],\
                [html.encode('utf8')])
                self.write_body(b)
                return

            if self.path.find('/files/')!=-1:
                self.write_file(self.path)
                return

            if self.path=='/lsusb':
                if self.user!='adm':
                    self.Redirect("/")
                    self.end_headers()
                    return
                devices=lsusb()
                html=""
                for k,d in devices.items():
                    html+="<tr><td>%s</td</tr>" % (k)
                b=self.write_pattern("/lsusb.html",['%devices%'],\
                [html.encode('utf8')])
                self.write_body(b)
                return

            if self.path.find('/printers')==0:
                if self.user!='adm':
                    self.Redirect("/")
                    self.end_headers()
                    return
                qresult=self.db.get(self.db.tb_printers._get())
                html=""
                for record in qresult:
                    pr=self.db.tb_printers.result2values(record)
                    pr['type_device']=dbDTPrint.TYPE_DEVICE[pr['type_device']]
                    pr['type_connect']=dbDTPrint.TYPE_CONNECT[pr['type_connect']]
                    html+="<tr onclick='window.location=\"/printers?id=%d\"'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%d</td></tr>\n" \
                    % (pr['id'],pr['name'],pr['vendor'],pr['type_connect'],pr['address'],pr['port'],pr['charset_device'])
                html=html.encode('utf8')
                b=self.write_pattern("/printers.html",['%printers%'],[html])
                e=""
                if get_vals.has_key('id'):
                    qresult=self.db.get(self.db.tb_printers._get(id=int(get_vals['id'])))
                    devserial=lsserial()
                    if len(qresult)>0:
                        pr=self.db.tb_printers.result2values(qresult[0])
                    else:
                        pr={'type_device':0,'type_connect':0,'device':0,'name':'','width':36,'dpi':384,'id':0,'interface':0,'id_vendor':'','id_product':'','vendor':'','byte1':'','byte2':'','address':'','port':'9600','charset_device':17,'charset_driver':'cp866','description':'','speed':115200,'usr_pass':'0001','adm_pass':'0030'}
                    if pr['type_connect']!=2:
                        pr['nethidden']='hidden'
                    else:
                        pr['usbhidden']=''
                    if pr['type_connect']!=1:
                        pr['usbhidden']='hidden'
                    else:
                        pr['usbhidden']=''
                    pr['type_device']=self.html_arr2select(dbDTPrint.TYPE_DEVICE,pr['type_device'])
                    pr['type_connect']=self.html_arr2select(dbDTPrint.TYPE_CONNECT,pr['type_connect'])
                    pr['device']=self.html_arrstr2select(devserial,pr['device'])
                    e=self.write_pattern_hash("/edprint.html",pr)
                b=b+e        
                self.write_body(b)
                return

            self.write_body(self.get_file(self.path))
        return


    def result_xml(self,id,data,tdata):
        if tdata=='':
            tdata='text'
        r= '<result>%d</result>' % id
        r+='<data type="%s">%s</data>' % (tdata,data)
        r+='</return>'
        if id!=0:
            self.db._log(self.client_address[0],self.user,'RESULT',self.path,self.XML,id)
        else:
            self.db._log(self.client_address[0],self.user,'CMD',self.path,self.XML,id)
        return r
        #.encode("utf8")

    def do_POST(self):
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={'REQUEST_METHOD':'POST',
                     'CONTENT_TYPE':self.headers['Content-Type'],
                     })
        
        if not self.mysql_open():
            self._do_HEAD("text/html",404)
            print "error. not open mysql"
            return
        else:
            self.db._read_sets()

        if (self.path.find("/login")==0):
            self.Redirect("/")
            self.WriteCookie(form)
            self.end_headers()
            return
        
        if form.has_key("login"):
            login=form['login'].value
        else:
            login=self.ReadCookie()
            if login is None:
                self.Redirect("/login")
                self.end_headers()
                return

        if not self.verify(login):
            self.Redirect("/login")
            self.end_headers()
            return

        self.db._log(self.client_address[0],self.user,'POST',self.path,'')

        if self.path=="/put_kkm_tabvalue":
            r=""
            if form.has_key("printer") and form.has_key("value"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_FPRINT':
                    try:
                        lock_printer(prn['id'])
                        if self.create_printer(prn):
                            xml_params="<list>\
                            <p><n>tabval</n><v>%s</v></p>\
                            <p><n>value</n><v>%s</v></p>\
                            <p><n>incrow</n><v>%s</v></p>\
                            <p><n>nvalues</n><v>%s</v></p>\
                            </list>" % (form["tabval"].value,form["value"].value,form["incrow"].value,1)
                            if self._do_print_kkm_fprint(prn=prn,cm_command="prn_tabset",cm_param=xml_params,xmlformat=False)==0:
                                r="0"
                            del self.ep
                    except:
                        r="1"
                    finally:
                        unlock_printer(prn['id'])
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_SHTRIHM':
                    try:
                        lock_printer(prn['id'])
                        if self.create_printer(prn):
                            xml_params="<list>\
                            <p><n>table</n><v>%s</v></p>\
                            <p><n>row</n><v>%s</v></p>\
                            <p><n>col</n><v>%s</v></p>\
                            <p><n>value</n><v>%s</v></p>\
                            </list>" % (form["table"].value,form["row"].value,form["col"].value,form["value"].value)
                            if self._do_print_kkm_shtrihm(prn=prn,cm_command="prn_tabset",cm_param=xml_params,xmlformat=False)==0:
                                r="0"
                            del self.ep
                    except:
                        r="1"
                    finally:
                        unlock_printer(prn['id'])
            self._writetxt(r)
            return

        if self.path=="/get_kkm_tabstrings":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_FPRINT':
                    try:
                        lock_printer(prn['id'])
                        if self.create_printer(prn):
                            xml_params="<list>\
                            <p><n>tabval</n><v>%s</v></p>\
                            <p><n>incrow</n><v>%s</v></p>\
                            <p><n>nvalues</n><v>%s</v></p>\
                            </list>" % (form["tabval"].value,form["incrow"].value,form["nvalues"].value)
                            if self._do_print_kkm_fprint(prn=prn,cm_command="prn_tabgets_CHR",cm_param=xml_params,xmlformat=False)==0:
                                r+=arr2htmtable(form["tabval"].value,self.ep.tabvalues,'onclick="changetabvalue(this,%id%);"')
                            del self.ep
                    except:
                        pass
                    finally:
                        unlock_printer(prn['id'])
            self._writetxt(r,encode=False)
            return

        if self.path=="/get_kkm_tables":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_SHTRIHM':
                    try:
                        lock_printer(prn['id'])
                        if self.create_printer(prn):
                            if self._do_print_kkm_shtrihm(prn=prn,cm_command="prn_get_tables",cm_param="",xmlformat=False)==0:
                                r=json.dumps(self.TablesStruct ,ensure_ascii=False)
                            del self.ep
                    except:
                        pass
                    finally:
                        unlock_printer(prn['id'])
            self._writetxt(r,encode=False)
            return

        if self.path=="/get_kkm_tabvalues":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_FPRINT':
                    try:
                        lock_printer(prn['id'])
                        if self.create_printer(prn):
                            if self._do_print_kkm_fprint(prn=prn,cm_command="prn_tabgets_BCD",cm_param="",xmlformat=False)==0:
                                r+=hash2htmtable(self.ep.tabvalues,3,'onclick="changetabvalue(this,0);"')
                            del self.ep
                    except:
                        pass
                    finally:
                        unlock_printer(prn['id'])
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_SHTRIHM':
                    table=form["table"].value
                    try:
                        lock_printer(prn['id'])
                        if self.create_printer(prn):
                            if self._do_print_kkm_shtrihm(prn=prn,cm_command="prn_get_tabvalues",cm_param="<list><p><n>table</n><v>"+table+"</v></p></list>",xmlformat=False)==0:
                                r=json.dumps(self.TablesValues ,ensure_ascii=False)
                            del self.ep
                        else:
                            r='0'
                    except:
                        pass
                    finally:
                        unlock_printer(prn['id'])
            self._writetxt(r,encode=False)
            return

        if self.path=="/get_kkm_status":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if self.create_printer(prn):
                    if self.do_print_def(prn=prn,cm_command="prn_devstatus",cm_param="",xmlformat=False)==0:
                        r+=hash2htmtable(self.ep.DEVICE,5)
                    del self.ep
            self._writetxt(r)
            return

        if self.path=="/set_kkm_renull":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if self.create_printer(prn):
                    result=self.do_print_def(prn=prn,cm_command="_renull",cm_param="",xmlformat=False)
                    r=str(result)
                    del self.ep

            self._writetxt(r)
            return

        if self.path=="/set_kkm_port":
            r=""
            if form.has_key("speed"):
                speed=form["speed"].value
            else:
                speed="115200"
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if self.create_printer(prn):
                    result=self.do_print_def(prn=prn,cm_command="_setport",cm_param="<list><p><n>speed</n><v>"+speed+"</v></p></list>",xmlformat=False)
                    r=str(result)
                    del self.ep

            self._writetxt(r)
            return

        if self.path=="/set_kkm_curtime":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if self.create_printer(prn):
                    result=self.do_print_def(prn=prn,cm_command="prn_setcurtime",cm_param="",xmlformat=False)
                    r=str(result)
                    del self.ep
            self._writetxt(r)
            return

        if self.path=="/set_kkm_curdate":
            r=""
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                if self.create_printer(prn):
                    result=self.do_print_def(prn=prn,cm_command="prn_setcurdate",cm_param="",xmlformat=False)
                    r=str(result)
                    del self.ep
            self._writetxt(r)
            return

        if self.path=="/cmd_list_html":
            if form.has_key("printer"):
                prname=form["printer"].value
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])

                if dbDTPrint.TYPE_DEVICE[prn['type_device']].find('ESCPOS')!=-1:
                    d=CMD_ESCPOS
                    i=0
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_FPRINT':
                    d=CMD_FPRINT
                    i=100
                if dbDTPrint.TYPE_DEVICE[prn['type_device']]=='KKM_SHTRIHM':
                    d=CMD_SHTRIHM
                    i=100

                r=""
                for v in d:
                    i+=1
                    r+="<option value='%d'>%s</option>\n" % (i,v)
            self._writetxt(r)
            return

        if self.path=="/cmd_info":
            if form.has_key("printers"):
                r='<?xml version="1.0" encoding="UTF-8"?>'
                r+="\n<return>"
                printers=self.db.get(self.db.tb_printers._get())
                for p in printers:
                    prn=self.db.tb_printers.result2values(p)
                    r+="<printer>%s</printer>\n" % prn['name']
                r+='</return>'
            if form.has_key("printer"):
                prname=form["printer"].value
                r='<?xml version="1.0" encoding="UTF-8"?>'
                r+="\n<return>"
                printer=self.db.get(self.db.tb_printers._get(name=prname))
                prn=self.db.tb_printers.result2values(printer[0])
                r+="<printer>\n"
                for k,v in prn.items():
                    r+="<%s>%s</%s>\n" % (k,v,k)
                r+="</printer>"
                r+='</return>'
            self._writetxt(r)
            return

        if self.path=="/cmd_autocreate":
            if form.has_key("printer"):
                r='<?xml version="1.0" encoding="UTF-8"?>'
                r+="\n<return>"
                d=lsserial("FTDI_USB")
                if len(d)!=0:
                    self.db.run(self.db.tb_printers._del(name="Fprint"))
                    pr={'type_device':2,\
                        'type_connect':0,\
                        'device':d[0],\
                        'name':'Fprint',\
                        'vendor':'',\
                        'description':'Default printer',\
                        'speed':115200}
                    self.db.run(self.db.tb_printers._add(pr))
                    self.db._packid()
                    p=self.db.get(self.db.tb_printers._get(name="Fprint"))
                    prn=self.db.tb_printers.result2values(p[0])
                    if self.create_printer(prn):
                        self._do_print_kkm_fprint(prn=prn,cm_command="prn_devstatus",cm_param="",xmlformat=False)
                        r+="0"
                        del self.ep
                d=lsserial("usb-ATOL")
                if len(d)!=0:
                    self.db.run(self.db.tb_printers._del(name="Fprint"))
                    pr={'type_device':2,\
                        'type_connect':0,\
                        'device':d[0],\
                        'name':'Fprint',\
                        'vendor':'',\
                        'description':'Default printer',\
                        'speed':115200}
                    self.db.run(self.db.tb_printers._add(pr))
                    self.db._packid()
                    p=self.db.get(self.db.tb_printers._get(name="Fprint"))
                    prn=self.db.tb_printers.result2values(p[0])
                    if self.create_printer(prn):
                        self._do_print_kkm_fprint(prn=prn,cm_command="prn_devstatus",cm_param="",xmlformat=False)
                        r+="0"
                        del self.ep
                d=lsserial("usb-FTDI")
                if len(d)!=0:
                    self.db.run(self.db.tb_printers._del(name="Shtrihm"))
                    pr={'type_device':3,\
                        'type_connect':0,\
                        'device':d[0],\
                        'name':'Shtrihm',\
                        'vendor':'shtrihm',\
                        'dpi':320,\
                        'width':40,\
                        'description':'Default printer',\
                        'speed':115200}
                    self.db.run(self.db.tb_printers._add(pr))
                    self.db._packid()
                    p=self.db.get(self.db.tb_printers._get(name="Shtrihm"))
                    prn=self.db.tb_printers.result2values(p[0])
                    if self.create_printer(prn):
                        self._do_print_kkm_shtrihm(prn=prn,cm_command="prn_devstatus",cm_param="",xmlformat=False)
                        r+="0"
                        del self.ep
                r+='</return>'
            self._writetxt(r)
            return

        if self.path=="/cmd_sets":
            r='<?xml version="1.0" encoding="UTF-8"?>'
            r+="\n<return>"
            if form.has_key("printer"):
                self.db.run(self.db.tb_printers._upd(form["printer"].value,form))
            r+='0</return>'
            self._writetxt(r)
            return

        if self.path=="/cmd":
            if form.has_key("xml"):
                r='<?xml version="1.0" encoding="UTF-8"?>'
                r+='<return>'
                self.XML = form["xml"].value
                try:
                    d=etree.fromstring(self.XML)
                except:
                    r+=self.result_xml(1,'error parsing. tag dtprint.',"text")
                    self._writetxt(r)
                    return
                if d.tag!='dtprint':
                    r+=self.result_xml(1,'error parsing. tag dtprint.',"text")
                    self._writetxt(r)
                    return
                p=d.find('printer')
                if p==None:
                    r+=self.result_xml(1,'error parsing. tag printer.',"text")
                    self._writetxt(r)
                    return
                prname=p.text
                qresult=self.db.get(self.db.tb_printers._get(name=prname))
                if (len(qresult)>0):
                    prn=self.db.tb_printers.result2values(qresult[0])
                else:
                    r+=self.result_xml(3,'error printer. not found.',"text")
                    self._writetxt(r)
                    return
                cmdlist=d.find('cmdlist')
                if cmdlist==None:
                    r+=self.result_xml(1,'error parsing. tag cmdlist.',"text")
                    self._writetxt(r)
                    return

                lock_printer(prn['id'])

                parse_error=False
                print_error=False
                paper_error=False
                cmd_result=""
                    
                try:
                    if not self.create_printer(prn):
                        print_error=True

                    if not(print_error):
                        for cmdline in cmdlist:
                            cm_command=cmdline.find('command')
                            cm_param=cmdline.find('param')
                            if (cm_command==None)or(cm_param==None):
                                parse_error=True
                            else:
                                ls=cm_param.find('list')
                                if ls!=None:
                                    cm_param=etree.tostring(ls)
                                else:
                                    cm_param=cm_param.text
                                cmd_result = self.do_print(prn,cm_command.text,cm_param)
                                if self.errcode!=0:
                                    break
                except:
                    print_error=True
                finally:
                    unlock_printer(prn['id'])

                if parse_error:
                    cmd_result=self.result_xml(1,'<comment>error parsing. tag cmd.</comment>',"text")
                if print_error:
                    cmd_result=self.result_xml(4,'<comment>error printer connect.</comment>',"text")

                """ RESULT XML """
                r+=cmd_result
                self._writetxt(r)
                if not print_error:
                    del self.ep
                return
            else:
                self._do_HEAD("text/html",404)
                self.end_headers()
                print "not exist file xml"
                return

        if (self.path.find("/sets")==0):
            if self.user!='adm':
                self.Redirect("/")
                self.end_headers()
                print "access denied"
                return
            for field in form.keys():
                fd=field
                val=form[field].value
                if field=='pass_adm':
                    if form[field].value=='':
                        continue
                    fd='password_adm'
                    val=md5(form[field].value).hexdigest()
                if field=='pass_usr':
                    if form[field].value=='':
                        continue
                    fd='password_usr'
                    val=md5(form[field].value).hexdigest()
                self.db.run(self.db.tb_sets._upd(fd,val))
            self.Redirect("/sets")
            self.end_headers()
            self.db._log(self.client_address[0],self.user,'WRITED',self.path,'')
            return
        
        if (self.path.find("/files")==0):
            result=''
            param=''
            if form.has_key("delete"): 
                os.remove('site/files/'+form['delete'].value)
                result="DELETE_FILE"
                param=form['delete'].value
            if form.has_key("file_image"): 
                if form['file_image'].filename:
                    if not (form.has_key('filename')) or form['filename'].value=='':
                        fn=form['file_image'].filename
                    else:
                        fn=form['filename'].value
                    file_data=form['file_image'].file.read()
                    self.put_file(file_data,'/files/'+fn)
                    del file_data
                    result="PUT_FILE"
                    param=fn
            self.Redirect("/files")
            self._writetxt(result)
            self.db._log(self.client_address[0],self.user,result,self.path,param)
            return

        if (self.path.find("/printers")==0):
            if self.user!='adm':
                self.Redirect("/")
                self.end_headers()
                print "access denied"
                return
            if form.has_key("_scan"):
                devices=lsusb()
                html=""
                onclick="onclick='onclick_tabscan(this);'"
                for k,d in devices.items():
                    html+="<tr %s >" % onclick
                    for r in d:
                        html+="<td>%s</td>" % (r)
                    html+="</tr>"
                b=self.write_pattern("/lsusb.html",['%devices%'],\
                [html])
                self._writetxt(b)
                return
            if form.has_key("_addnew"):
                n=form['name'].value
                self.db._add_printer(n.encode('utf8'))
                self.db._log(self.client_address[0],self.user,'ADD_PRINTER',self.path,n)

            if form.has_key("codetest"):
                self.XML=""
                qresult=self.db.get(self.db.tb_printers._get(id=int(form['id'].value)))
                if (len(qresult)>0):
                    prn=self.db.tb_printers.result2values(qresult[0])
                    lock_printer(prn['id'])
                    try:
                        self.create_printer(prn)
                        self.do_print(prn,'print_text','Print test codepage:\n')
                        for i in range(64):
                            j=i
                            text=u'code=%d. [Тестовая печать]' % j
                            prn['charset_device']=j
                            self.do_print(prn,'set_style','b;normal;a;left;')
                            self.do_print(prn,'print_text',text)
                        self.do_print(prn,'print_text',"\n\n")
                        self.do_print(prn,'cut',"")
                        del self.ep
                    except:
                        print "error test print"
                    finally:
                        unlock_printer(prn['id'])

            if form.has_key("edpr"):
                idpr=int(form['id'].value)
                if (idpr==0):
                    print self.db.tb_printers._add(form)
                    self.db.run(self.db.tb_printers._add(form))
                    self.db._packid()
                else:
                    self.db.run(self.db.tb_printers._upd(int(form['id'].value),form))
                self.db._log(self.client_address[0],self.user,'EDIT_PRINTER',self.path,form['id'].value)
            if form.has_key("delpr"):
                self.db.run(self.db.tb_printers._del(id=int(form['id'].value)))
                self.db._log(self.client_address[0],self.user,'DEL_PRINTER',self.path,form['id'].value)
            self.Redirect("/printers")
            self.end_headers()
            return


        self.send_response(200)
        self.end_headers()

        return

class ThreadedHTTPServer(ThreadingMixIn, HTTPServer):
    """ Создаем веб сервер многопоточный """

if __name__ == '__main__':
    db = dbDTPrint.dbDTPrint(dbDTPrint.DATABASE, 'localhost', dbDTPrint.MYSQL_USER, dbDTPrint.MYSQL_PASSWORD) 
    if db.open():
        db._log('localhost','sys','db_start','/','')
    else:
        print "DTPWeb Server down. Database not exist"
        sys.exit(1)

    db._read_sets()
    create_prlocks()

    server = ThreadedHTTPServer((db.sets['server_ip'], int(db.sets['server_port'])), Handler)
    #server = ThreadedHTTPServer((db.sets['server_ip'], 10100), Handler)
    
    db._log('localhost','sys','web_start','/','')
    print 'Start DTPWeb Server v %s [%s]' % (VERSION,db.sets['server_port'])
    db.close()
    
    server.serve_forever()

