#!/usr/bin/python
# -*- coding: utf-8

"""
    Web Client for DTPrint
    License GPL
    writed by Romanenko Ruslan
    redeyser@gmail.com
"""
import httplib, urllib
import xml.etree.ElementTree as etree

TYPE_DEVICE     = ['ESCPOS','ESCPOS_OLD','KKM_FPRINT','KKM_SHTRIHM']

ERROR_CODE      = {
    "0"     : u"Без ошибок",\
    "1"     : u":Ошибка протокола",\
    "2"     : u":Ошибка драйвера",\
    "4"     : u":Устройство не найдено",\
    "140"   : u":Неверный пароль",\
}

class DTPclient:

    def __init__(self,server_ip,server_port,password):
        self.server_ip=server_ip
        self.server_port=server_port
        self.password=password
        self.use_cut=True
        self.err_ignore=False

    def connect(self):
        try:
            #print "connect:%s:%d" % (self.server_ip,self.server_port)
            self.conn = httplib.HTTPConnection("%s:%d" % (self.server_ip,self.server_port))
            return True
        except:
            print "not connect"
            return False

    def request(self,page,params):
        self.data=""
        if not self.connect():
            print "error connect"
            return False
        params.update({"login":self.password})
        params=urllib.urlencode(params)
        headers = {"Content-type": "application/x-www-form-urlencoded","Accept": "text/xml"}
        try:
            self.conn.request("POST",page,params,headers)
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

    def _get_printers(self):
        self.printers=[]
        if not self.request("/cmd_info",{"printers":1}):
            return False
        try:
            xml=etree.fromstring(self.data)
            if xml==None and xml.tag!='return':
                return False
            for line in xml:
                if line.tag=="printer":
                    self.printers.append(line.text)
        except:
            xml=None
            return False
        return True
        
    def _get_printer_info(self,printer):
        self.result="1"
        self._result()
        self.printer_info={}
        if not self.request("/cmd_info",{"printer":printer}):
            return False
        try:
            xml=etree.fromstring(self.data)
            if xml==None and xml.tag!='return':
                return False
            p=xml.find("printer")
            for line in p:
                self.printer_info[line.tag]=line.text
        except:
            xml=None
            return False
        self.printer_info['type_device']=TYPE_DEVICE[int(self.printer_info['type_device'])]
        self.result="0"
        self._result()
        return True

    def _cmd_autocreate(self,printer):
        if not self.request("/cmd_autocreate",{"printer":printer}):
            return False
        try:
            xml=etree.fromstring(self.data)
            if xml==None and xml.tag!='return':
                return False
            if xml.text!="0":
                return False
        except:
            xml=None
            return False
        return True

    def _set_printer_info(self,printer,param,value):
        self.result="1"
        self._result()
        if not self.request("/cmd_sets",{"printer":printer,param:value}):
            return False
        try:
            xml=etree.fromstring(self.data)
            if xml==None and xml.tag!='return':
                return False
            if xml.text!="0":
                return False
        except:
            xml=None
            return False
        self.result="0"
        self._result()
        return True
        
    def _xml_clear(self,printer):
        self.xml="<?xml version=\"1.0\" encoding=\"UTF-8\"?><dtprint><printer>%s</printer><cmdlist>##list##</cmdlist></dtprint>" % printer
        self.cmdlist=""

    def _result(self):
        if ERROR_CODE.has_key(self.result):
            self.result_name=ERROR_CODE[self.result]
        else:
            self.result_name=u":Ошибка драйвера: "+self.result

    def _xml_add(self,command,hparams):
        p=""
        for k,v in hparams.items():
            if type(v) == list:
                sv=""
                for i in range(len(v)):
                    sv=sv+"<sv id=\"%d\">%s</sv>\n" % (i,v[i])
                p+="<p type=\"array\"><n>%s</n><v>%s</v></p>" % (k,sv)
            else:
                p+="<p><n>%s</n><v>%s</v></p>" % (k,v)

        self.cmdlist+="<cmd><command>%s</command>\n<param><list>%s</list></param></cmd>\n" % (command,p)

    def _xml_close(self):
        self.xml=self.xml.replace("##list##",self.cmdlist).encode("utf8")

    def _xml_pack(self):
        self.xml=self.xml.replace("&","&amp;")

    def _cmd(self):
        self.return_data={}
        self.result="1"
        self._result()
        self._xml_pack()
        #print self.xml
        if not self.request("/cmd",{"xml":self.xml}):
            return False
        try:
            #print self.data
            xml=etree.fromstring(self.data)
            if xml==None and xml.tag!='return':
                print "error xml parsing"
                return False
            r=xml.find("result")
            self.result=r.text
            self._result()
            data=xml.find("data")
            t='text'
            if data!=None:
                #print etree.tostring(data)
                #print data.items()
                if len(data.items())!=0:
                    if data.items()[0][0]=='type':
                        t=data.items()[0][1]
                if t=='text':
                    self.return_data=data.text
                if t=="hash":
                    self.return_data={}
                    for d in data:
                        self.return_data[d.tag]=d.text
                if t=="array":
                    self.return_data=[]
                    for d in data:
                        if d.text==None:
                            t=''
                        else:
                            t=d.text
                        self.return_data.append(t)
        except:
            if self.err_ignore:
                return True
            else:
                return False

        if self.result=='0' or self.err_ignore:
            return True
        else:
            return False

    def _cmd_prn_devstatus(self,printer):
        self._xml_clear(printer)
        self._xml_add("prn_devstatus",{})
        self._xml_close()
        r=self._cmd()
        if type(self.return_data)==dict:
            if self.return_data.has_key("dt_date"):
                pass
                #d=self.return_data['dt_date']
                #self.return_data['dt_date']=d[6:8]+"."+d[3:5]+"."+d[0:2]
            if self.return_data.has_key("dt_time"):
                self.return_data['dt_time']=self.return_data['dt_time'].replace(".",":")
        return r

    def _cmd_prn_setcurdatetime(self,printer):
        self._xml_clear(printer)
        self._xml_add("prn_setcurtime",{})
        self._xml_add("prn_setcurdate",{})
        self._xml_close()
        r=self._cmd()
        return r

    def _cmd_prn_tabget_textlines(self,printer):
        self._xml_clear(printer)
        self._xml_add("prn_get_tabvalues",{"table":"4"})
        self._xml_close()
        r=self._cmd()
        return r

    def _cmd_prn_tabgets_CHR(self,printer):
        self._xml_clear(printer)
        self._xml_add("prn_tabgets_CHR",{"tabval":"textlines","incrow":"0","nvalues":"20"})
        self._xml_close()
        r=self._cmd()
        return r

    def _cmd_prn_tabset(self,printer,values):
        self._xml_clear(printer)
        self._xml_add("prn_tabset",{"tabval":"textlines","incrow":"0","nvalues":"20","value":values})
        self._xml_close()
        r=self._cmd()
        return r

    def _cmd_prn_tabset_shtrih(self,printer,row,value):
        self._xml_clear(printer)
        self._xml_add("prn_tabset",{"table":4,"row":row,"col":1,"value":value})
        self._xml_close()
        r=self._cmd()
        return r

    def _cm(self,printer,cmd,hdata):
        #print printer,cmd,hdata
        if cmd=='_cut' and not self.use_cut:
            return True
        if printer=='None' or printer==None:
            self.return_data=""
            return True
        self._xml_clear(printer)
        self._xml_add(cmd,hdata)
        self._xml_close()
        r=self._cmd()
        return r


    def _cmd_prn_sounddw(self,printer):
        return self._cm(printer,"prn_sound_dartweider",{})

    def _cmd_reportX(self,printer,_type):
        return self._cm(printer,"_reportX",{'type':_type})

"""
client = DTPclient("localhost",10111,"dtpadm")
print client._cmd_prn_tabgets_CHR("Fprint")
print client.result
print client.return_data
"""
