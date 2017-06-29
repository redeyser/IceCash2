#!/usr/bin/python
# -*- coding: utf-8

import httplib, urllib,time
import requests
import xml.etree.ElementTree as etree
import re
from my import curdate2my
from datetime import datetime
import dbIceCash as db
ns={\
"c":"http://fsrar.ru/WEGAIS/Common",\
"wbr":"http://fsrar.ru/WEGAIS/TTNInformBReg",\
"pref":"http://fsrar.ru/WEGAIS/ProductRef",\
"oref":"http://fsrar.ru/WEGAIS/ClientRef",\
"rc":"http://fsrar.ru/WEGAIS/ReplyClient",\
"ns":"http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01",\
"wb":"http://fsrar.ru/WEGAIS/TTNSingle",\
"xsi":"http://www.w3.org/2001/XMLSchema-instance",\
"wt":"http://fsrar.ru/WEGAIS/ConfirmTicket",
"qp":"http://fsrar.ru/WEGAIS/QueryParameters",\
'tc':"http://fsrar.ru/WEGAIS/Ticket",\
"rst":"http://fsrar.ru/WEGAIS/ReplyRests",\
'wa':"http://fsrar.ru/WEGAIS/ActTTNSingle_v2",\
'ttn':"http://fsrar.ru/WEGAIS/ReplyNoAnswerTTN",\
}

XML_GET_CLIENTS=u"""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ns:Documents Version=\"1.0\"
xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"
xmlns:ns=\"http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01\"
xmlns:oref=\"http://fsrar.ru/WEGAIS/ClientRef\"
xmlns:qp=\"http://fsrar.ru/WEGAIS/QueryParameters\">
<ns:Owner>
    <ns:FSRAR_ID>%fsrar_id%</ns:FSRAR_ID>
</ns:Owner>
<ns:Document>
    <ns:QueryClients>
        <qp:Parameters>
            <qp:Parameter>
            <qp:Name>ИНН</qp:Name>
            <qp:Value>%INN%</qp:Value>
        </qp:Parameter>
        </qp:Parameters>
    </ns:QueryClients>
</ns:Document>
</ns:Documents>
"""

XML_SEND_WAYBILL_HEAD="""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ns:Documents Version="1.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:ns= "http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
xmlns:c="http://fsrar.ru/WEGAIS/Common"
xmlns:oref="http://fsrar.ru/WEGAIS/ClientRef"
xmlns:pref="http://fsrar.ru/WEGAIS/ProductRef"
xmlns:wb="http://fsrar.ru/WEGAIS/TTNSingle">
<ns:Owner>
<ns:FSRAR_ID>%fsrar_id%</ns:FSRAR_ID>
</ns:Owner>
<ns:Document>
<ns:WayBill>
<wb:Identity>%identity%</wb:Identity>

<wb:Header>
<wb:NUMBER>%number%</wb:NUMBER>
<wb:Date>%dt%</wb:Date>
<wb:ShippingDate>%dt%</wb:ShippingDate>
<wb:Type>%type%</wb:Type>
<wb:UnitType>%packet%</wb:UnitType>

<wb:Shipper>
<oref:INN>%inn%</oref:INN><oref:KPP>%kpp%</oref:KPP><oref:ClientRegId>%regid%</oref:ClientRegId>
<oref:ShortName>%name%</oref:ShortName><oref:FullName>%name%</oref:FullName>
<oref:address>
    <oref:Country>643</oref:Country><oref:description></oref:description>
</oref:address>
</wb:Shipper>

<wb:Consignee>
<oref:INN>%send_inn%</oref:INN><oref:KPP>%send_kpp%</oref:KPP><oref:ClientRegId>%send_regid%</oref:ClientRegId>
<oref:ShortName>%send_name%</oref:ShortName><oref:FullName>%send_name%</oref:FullName>
<oref:address>
    <oref:Country>643</oref:Country><oref:description></oref:description>
</oref:address>
</wb:Consignee>

<wb:Transport>
<wb:TRAN_CAR></wb:TRAN_CAR>
<wb:TRAN_CUSTOMER></wb:TRAN_CUSTOMER>
<wb:TRAN_DRIVER></wb:TRAN_DRIVER>
<wb:TRAN_LOADPOINT></wb:TRAN_LOADPOINT>
<wb:TRAN_UNLOADPOINT></wb:TRAN_UNLOADPOINT>
<wb:TRAN_FORWARDER></wb:TRAN_FORWARDER>
</wb:Transport>

</wb:Header>

<wb:Content>
%content%
</wb:Content>
</ns:WayBill>
</ns:Document>
</ns:Documents>
"""

XML_SEND_WAYBILL_CONTENT="""
<wb:Position>
<wb:Quantity>%quantity%</wb:Quantity><wb:Price>%price%</wb:Price><wb:Identity>%identity%</wb:Identity><wb:InformA><pref:RegId>%inform_a%</pref:RegId></wb:InformA>
<wb:InformB><pref:InformBItem><pref:BRegId>%inform_b%</pref:BRegId></pref:InformBItem></wb:InformB>
<wb:Product>

<pref:Type>%pref_type%</pref:Type><pref:FullName>%shortname%</pref:FullName>
<pref:ShortName>%shortname%</pref:ShortName>
<pref:AlcCode>%alccode%</pref:AlcCode>
<pref:Capacity>%capacity%</pref:Capacity>
<pref:AlcVolume>%alcvolume%</pref:AlcVolume>
<pref:ProductVCode>%productvcode%</pref:ProductVCode>

<pref:Producer>
<oref:INN>%inn%</oref:INN><oref:KPP>%kpp%</oref:KPP>
<oref:ClientRegId>%regid%</oref:ClientRegId><oref:ShortName>%oref_shortname%</oref:ShortName>
<oref:FullName>%oref_shortname%</oref:FullName>
<oref:address>
    <oref:Country>643</oref:Country><oref:description></oref:description>
</oref:address>
</pref:Producer>

</wb:Product>
</wb:Position>
"""

XML_SEND_ACT="""<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<ns:Documents Version=\"1.0\"
xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"
xmlns:ns= \"http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01\"
xmlns:oref=\"http://fsrar.ru/WEGAIS/ClientRef\"
xmlns:pref=\"http://fsrar.ru/WEGAIS/ProductRef\"
xmlns:wa= \"http://fsrar.ru/WEGAIS/ActTTNSingle\">
<ns:Owner>
    <ns:FSRAR_ID>%fsrar_id%</ns:FSRAR_ID>
</ns:Owner>
<ns:Document>
  <ns:WayBillAct_v2>
    <wa:Header>
        <wa:IsAccept>%accept%</wa:IsAccept>
        <wa:ACTNUMBER>%iddoc%</wa:ACTNUMBER>
        <wa:ActDate>%date%</wa:ActDate>
        <wa:WBRegId>%wb_RegId%</wa:WBRegId>
        <wa:Note></wa:Note>
    </wa:Header>
    <wa:Content>
        %content%
    </wa:Content>
  </ns:WayBillAct_v2>
</ns:Document>
</ns:Documents>
"""

XML_ACT_CONTENT="""
<wa:Position>
\t<wa:Identity>%identity%</wa:Identity>
\t<wa:InformF2RegId>%wb_RegId%</wa:InformF2RegId>
\t<wa:RealQuantity>%real%</wa:RealQuantity>
</wa:Position>
"""
XML_CHECK="""<?xml version="1.0" encoding="UTF-8"?>
<Cheque
inn="%inn%"
datetime="%datetime%"
kpp="%kpp%"
kassa="%kassa%"
address="%address%"
name="%name%"
number="%ncheck%"
shift="1"
>
%bottles%
</Cheque>
"""

XML_BOTTLE="""
\t<Bottle barcode="%barcode%"
\tean="%ean%" price="%price%" %litrag%/>
"""

XML_GET_OSTAT="""<?xml version="1.0" encoding="UTF-8"?>
<ns:Documents Version="1.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:ns="http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
xmlns:qp="http://fsrar.ru/WEGAIS/QueryParameters">
<ns:Owner>
<ns:FSRAR_ID>%fsrar_id%</ns:FSRAR_ID>
</ns:Owner>
<ns:Document>
<ns:QueryRests></ns:QueryRests>
</ns:Document>
</ns:Documents>
"""

XML_GET_REPLY="""<?xml version="1.0" encoding="UTF-8"?>
<ns:Documents Version="1.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:ns="http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
xmlns:qp="http://fsrar.ru/WEGAIS/QueryParameters"
>
<ns:Owner>
    <ns:FSRAR_ID>%fsrar_id%</ns:FSRAR_ID>
</ns:Owner>
<ns:Document>
    <ns:QueryResendDoc>
    <qp:Parameters>
        <qp:Parameter>
            <qp:Name>WBREGID</qp:Name>
            <qp:Value>%ttn%</qp:Value>
        </qp:Parameter>
    </qp:Parameters>
    </ns:QueryResendDoc>
</ns:Document>
</ns:Documents>
"""

XML_GET_NATTN="""<?xml version="1.0" encoding="UTF-8"?>
<ns:Documents Version="1.0"
xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
xmlns:ns="http://fsrar.ru/WEGAIS/WB_DOC_SINGLE_01"
xmlns:qp="http://fsrar.ru/WEGAIS/QueryParameters">

<ns:Owner>
    <ns:FSRAR_ID>%fsrar_id%</ns:FSRAR_ID>
</ns:Owner>
<ns:Document>
    <ns:QueryNATTN>
    <qp:Parameters>
        <qp:Parameter>
            <qp:Name>КОД</qp:Name>
            <qp:Value>%fsrar_id%</qp:Value>
        </qp:Parameter>
    </qp:Parameters>
    </ns:QueryNATTN>
</ns:Document>
</ns:Documents>
"""

class EgaisClient:

    def __init__(self,server_ip,server_port,db):
        self.server_ip=server_ip
        self.server_port=server_port
        self.db=db

    def assm(self,page):
        return "http://%s:%d%s" % (self.server_ip,self.server_port,page)

    def _delete(self,page):
        print "delete %s" % page
        requests.delete(page)
        return True

    def _get(self,page):
        self.data=""
        try:
            r = requests.get(page)
            if r.status_code!=200:
                print "error_status"
                return False
            self.data=r.text.encode("utf8")
        except:
            return False
        return True

    def _post(self,page,params):
        self.data=""
        r=requests.post(page, data=params)
        self.data=r.content
        if r.status_code!=200:
            print "error_status"
            return False
        return True

    def _sendfile(self,url,pname,fname):
        files = {pname : open(fname, 'rb')}
        r = requests.post(url, files=files)
        if r.status_code!=200:
            print "error_status"
            self.data=r.content
            return False
        self.data=r.content
        return True

    def _connect(self):
        if self._get(self.assm("/")):
            r=re.search("FSRAR-RSA-(\d+)",self.data)
            if not r:
                return False
            self.fsrar_id=r.group(1)
            return True
        else:
            self.fsrar_id=""
            return False

    def _sendxml(self,fname,page,xml):
        f=open(fname,"w")
        f.write(xml)
        f.close()
        return self._sendfile(self.assm(page),'xml_file',fname)

    def _send_places(self):
        if not self._connect():
            return False
        xml=XML_GET_CLIENTS.replace("%INN%",self.db.sets['inn'])
        xml=xml.replace("%fsrar_id%",self.fsrar_id).encode("utf8")
        r=self._sendxml("client.xml","/opt/in/QueryPartner",xml)
        return r

    def _send_ostat(self):
        if not self._connect():
            return False
        xml=XML_GET_OSTAT.replace("%INN%",self.db.sets['inn'])
        xml=xml.replace("%fsrar_id%",self.fsrar_id).encode("utf8")
        r=self._sendxml("rest.xml","/opt/in/QueryRests",xml)
        return r

    def _send_reply(self,ttn):
        if not self._connect():
            return False
        xml=XML_GET_REPLY.replace("%ttn%",ttn)
        xml=xml.replace("%fsrar_id%",self.fsrar_id).encode("utf8")
        r=self._sendxml("reply.xml","/opt/in/QueryResendDoc",xml)
        return r

    def _send_nattn(self):
        if not self._connect():
            return False
        #self.db._truncate(db.TB_EGAIS_DOCS_NEED)
        xml=XML_GET_NATTN.replace("%fsrar_id%",self.fsrar_id)
        #.encode("utf8")
        r=self._sendxml("nattn.xml","/opt/in/QueryNATTN",xml)
        return r

    def _get_ticket(self):
        self.sign=""
        #print self.data
        tree=etree.fromstring(self.data)
        url  = tree.find("url")
        sign = tree.find("sign")
        if url==None:
            return ""
        if sign!=None:
            self.sign=sign.text
        return url.text

    def _send_act(self,id):
        if not self._connect():
            return False
        xml=self._make_act(id)
        if xml=="":
            return False
        r=self._sendxml("client.xml","/opt/in/WayBillAct",xml)

        reply_id=self._get_ticket()

        if reply_id!="":
            self.db.egais_docs_hd_upd(id,{'status':3,'reply_id':reply_id})
        return r

    def _send_return(self,id):
        if not self._connect():
            return False
        xml=self._make_return(id)
        if xml=="":
            return False
        r=self._sendxml("return.xml","/opt/in/WayBill",xml)

        reply_id=self._get_ticket()

        if reply_id!="":
            self.db.egais_docs_hd_upd(id,{'status':3,'reply_id':reply_id})
        return r

    def _send_check(self,_type,ncheck,pos):
        if not self._connect():
            return False
        xml=self._make_check(_type,ncheck,pos)
        if xml=="":
            return False
        print "-"*80
        print xml
        print "-"*80
        #return False
        r=self._sendxml("cheque.xml","/xml",xml)
        
        self.url=self._get_ticket()

        if self.url=="" or self.sign=="":
            return False
        return r

    def _send_move(self,id):
        if not self._connect():
            return False
        xml=self._make_move(id)
        if xml=="":
            return False
        r=self._sendxml("move.xml","/opt/in/WayBill",xml)

        reply_id=self._get_ticket()

        if reply_id!="":
            self.db.egais_docs_hd_upd(id,{'status':3,'reply_id':reply_id})
        return r

    def _create_return(self,id,idd):
        if self.db.egais_get_mydoc(id):
            struct={\
            "type":1,\
            "status":1,\
            "ns_FSRAR_ID"       :self.db.egais_doc_hd['recv_RegId'],\
            "wb_Identity"       :"0",\
            "ns_typedoc"        :"WayBill",\
            
            "wb_Date"           :curdate2my(),\
            "wb_ShippingDate"   :curdate2my(),\
            "wb_Type"           :"WBReturnFromMe",\
            "wb_UnitType"       :self.db.egais_doc_hd['wb_UnitType'],\

            "send_INN"          :self.db.egais_doc_hd['recv_INN'],\
            "send_KPP"          :self.db.egais_doc_hd['recv_KPP'],\
            "send_ShortName"    :self.db.egais_doc_hd['recv_ShortName'],\
            "send_RegId"        :self.db.egais_doc_hd['recv_RegId'],\

            "recv_INN"          :self.db.egais_doc_hd['send_INN'],\
            "recv_KPP"          :self.db.egais_doc_hd['send_KPP'],\
            "recv_ShortName"    :self.db.egais_doc_hd['send_ShortName'],\
            "recv_RegId"        :self.db.egais_doc_hd['send_RegId'],\
            }
            id=self.db.egais_docs_hd_add(struct)
            if id==0:
                return False
            self.db.egais_docs_hd_upd(id,{"wb_Identity":str(id),"wb_NUMBER":u"В"+self.db.sets['idplace'].rjust(3,"0")+str(id).rjust(4,"0")} )
            for rec in self.db.egais_doc_ct:
                if int(rec['id'])==idd:
                    struct=rec
                    struct["iddoc"]=id
                    struct["wb_Identity"]="1"
                    struct["pref_Type"]=u"АП"
                    del struct['id']
                    self.db.egais_docs_ct_add(struct)
            return True
        else:
            return False


    def _delete_in(self,id):
        for d in self.data_url_in:
            if id==d['idd']:
                self._delete(d['url'])

    def _get_docs_in(self):
        self.data_url_in=[]
        if self._get(self.assm("/opt/in")):
            try:
                d=etree.fromstring(self.data)
            except:
                return False
            for t in d:
                if t.tag!='url':
                    continue
                if t.attrib.has_key('replyId'):
                    id=t.attrib['replyId']
                else:
                    id=""
                url=t.text
                self.data_url_in.append({'idd':id,'url':url})
            return True
        else:
            return False

    def _get_docs_out(self):
        self.data_url=[]
        if self._get(self.assm("/opt/out")):
            try:
                d=etree.fromstring(self.data)
            except:
                return False
            for t in d:
                if t.tag!='url':
                    continue
                if t.attrib.has_key('replyId'):
                    id=t.attrib['replyId']
                else:
                    id=""
                url=t.text
                self.data_url.append({'idd':id,'url':url})
            return True
        else:
            return False

    def _dodoc(self):
        res={}
        for d in self.data_url:
            id=d['idd']
            url=d['url']
            if not self._get(url):
                continue    
            tree=etree.fromstring(self.data)
            doc = tree.find("ns:Document",ns)
            if doc==None:
                continue    

            typedoc=doc[0].tag
            #print typedoc

            if typedoc=="{%s}ConfirmTicket" % ns["ns"]:
                if self._addConfirmTicket(url,id,tree):
                    if res.has_key("ConfirmTicket"):
                        res['ConfirmTicket']+=1
                    else:
                        res['ConfirmTicket']=1
                    print "ConfirmTicket"
                    self._delete_in(id)
                    self._delete(url)
                    pass

            if typedoc=="{%s}Ticket" % ns["ns"]:
                if self._addTicket(url,id,tree):
                    if res.has_key("Ticket"):
                        res['Ticket']+=1
                    else:
                        res['Ticket']=1
                    print "Ticket"
                    self._delete_in(id)
                    pass
                self._delete(url)

            if typedoc=="{%s}ReplyClient" % ns["ns"]:
                if res.has_key("ReplyClient"):
                    res['ReplyClient']+=1
                else:
                    res['ReplyClient']=1
                print "ReplyClient"
                self._addplaces(doc[0])
                self._delete_in(id)
                self._delete(url)

            if typedoc=="{%s}ReplyRests" % ns["ns"]:
                res['ReplyRests.Products']=self._reload_ostat(doc[0])
                self._delete_in(id)
                self._delete(url)

            if typedoc=="{%s}WayBill" % ns["ns"]:
                if self._addWayBill(url,id,tree):
                    if res.has_key("WayBill"):
                        res['WayBill']+=1
                    else:
                        res['WayBill']=1
                    self._delete(url)
                    pass

            if typedoc=="{%s}WayBillAct" % ns["ns"] or typedoc=="{%s}WayBillAct_v2" % ns["ns"]:
                if self._addWayBillAct(url,id,tree):
                    if res.has_key("WayBillAct"):
                        res['WayBillAct']+=1
                    else:
                        res['WayBillAct']=1
                    self._delete(url)
                    pass

            if typedoc=="{%s}TTNInformBReg" % ns["ns"]:
                if self._addInformBReg(url,id,tree):
                    if res.has_key("TTNInformBReg"):
                        res['TTNInformBReg']+=1
                    else:
                        res['TTNInformBReg']=1
                    self._delete(url)
                    pass

            if typedoc=="{%s}ReplyNoAnswerTTN" % ns["ns"]:
                res['ReplyNoAnswerTTN']=self._read_nattn(doc[0])
                self._delete_in(id)
                self._delete(url)
        
        return res

    def _recalc(self):
        docs=self.db.egais_get_mydocs(0,None,None,None,None)
        for d in docs:
            iddoc=int(d['id'])
            tree=etree.fromstring(d['xml_inform'].encode('utf8'))
            if tree=="":
                continue
            if not self.db.egais_get_mydoc(iddoc):
                continue
            content=self._readhead_InformBReg(tree)
            for pos in content.findall("wbr:Position",ns):
                self.struct={}
                id=self._readcontent_InformBReg(pos)
                self.db.egais_docs_ct_updId(iddoc,id,self.struct)
        return True

    def _addplaces(self,tree):
        clients=tree.find("rc:Clients",ns)
        if clients==None:
            print "no clients"
            return
        struct={}
        self.db.egais_places_clear()
        for t in clients.findall("rc:Client",ns):
            a=t.find("oref:address",ns)
            for f in self.db.tb_egais_places.record_add:
                r=t.find("oref:"+f,ns)
                if r!=None:
                    struct[f]=r.text
                else:
                    r=a.find("oref:"+f,ns)
                    if r!=None:
                        struct[f]=r.text
            self.db.egais_places_add(struct)

    def _setstruct(self,base,tag,field=None):
        t=base.find(tag,ns)
        if field==None:
            field=tag.replace(":","_")
        try:
            self.struct[field]=t.text
            return True
        except:
            print "error:%s" % tag
            return False


    def _readhead_WayBill(self,tree):
        owner=tree.find("ns:Owner",ns)
        doc=tree.find("ns:Document",ns)
        doc=doc[0]
        header=doc.find("wb:Header",ns)
        shipper=header.find("wb:Shipper",ns)
        consignee=header.find("wb:Consignee",ns)

        self._setstruct(owner,"ns:FSRAR_ID")
        self._setstruct(doc,"wb:Identity")

        self._setstruct(header,"wb:NUMBER")
        self._setstruct(header,"wb:Date")
        self._setstruct(header,"wb:ShippingDate")
        self._setstruct(header,"wb:Type")
        self._setstruct(header,"wb:UnitType")

        self._setstruct(shipper,"oref:INN","send_INN")
        self._setstruct(shipper,"oref:KPP","send_KPP")
        self._setstruct(shipper,"oref:ShortName","send_ShortName")
        self._setstruct(shipper,"oref:ClientRegId","send_RegId")

        self._setstruct(consignee,"oref:INN","recv_INN")
        self._setstruct(consignee,"oref:KPP","recv_KPP")
        self._setstruct(consignee,"oref:ShortName","recv_ShortName")
        self._setstruct(consignee,"oref:ClientRegId","recv_RegId")

        content=doc.find("wb:Content",ns)
        return content

    def _readhead_InformBReg(self,tree):
        owner=tree.find("ns:Owner",ns)
        doc=tree.find("ns:Document",ns)
        doc=doc[0]
        header=doc.find("wbr:Header",ns)
        shipper=header.find("wbr:Shipper",ns)
        consignee=header.find("wbr:Consignee",ns)

        self._setstruct(shipper,"oref:ClientRegId","send_RegId")
        self._setstruct(consignee,"oref:ClientRegId","recv_RegId")
        self._setstruct(header,"wbr:WBNUMBER")
        self._setstruct(header,"wbr:WBRegId","tc_RegId")
        self._setstruct(header,"wbr:Identity")

        content=doc.find("wbr:Content",ns)
        return content

    def _readhead_Ticket(self,tree):
        doc=tree.find("ns:Document",ns)
        doc=doc[0]
        self._setstruct(doc,"tc:RegID")
        oper=doc.find("tc:OperationResult",ns)
        if oper!=None:
            self._setstruct(oper,"tc:OperationResult")
            self._setstruct(oper,"tc:OperationName")
        regid=self.struct['tc_RegID']
        del self.struct['tc_RegID']
        return regid

    def _readhead_ConfirmTicket(self,tree):
        doc=tree.find("ns:Document",ns)
        doc=doc[0]
        header=doc.find("wt:Header",ns)
        self._setstruct(header,"wt:WBRegId")
        self._setstruct(header,"wt:IsConfirm")
        regid=self.struct['wt_WBRegId']
        del self.struct['wt_WBRegId']
        return regid

    def _readhead_WayBillAct(self,tree):
        doc=tree.find("ns:Document",ns)
        doc=doc[0]
        header=doc.find("wa:Header",ns)
        self._setstruct(header,"wa:WBRegId")
        self._setstruct(header,"wa:IsAccept")
        regid=self.struct['wa_WBRegId']
        del self.struct['wa_WBRegId']
        return regid

    def _readcontent_WayBill(self,pos):
        informA=pos.find("wb:InformA",ns)
        informB=pos.find("wb:InformB",ns)
        informB=informB.find("pref:InformBItem",ns)
        product=pos.find("wb:Product",ns)
        producer=product.find("pref:Producer",ns)

        self._setstruct(pos,"wb:Identity")
        self._setstruct(pos,"wb:Quantity")
        self._setstruct(pos,"wb:Price")
        self._setstruct(pos,"wb:Pack_ID")
        self._setstruct(pos,"wb:Party")

        self._setstruct(informA,"pref:RegId")
        self._setstruct(informB,"pref:BRegId")

        self._setstruct(product,"pref:Type")
        if not self._setstruct(product,"pref:ShortName"):
            self._setstruct(product,"pref:FullName","pref_ShortName")
        self._setstruct(product,"pref:AlcCode")
        self._setstruct(product,"pref:Capacity")
        self._setstruct(product,"pref:AlcVolume")
        self._setstruct(product,"pref:ProductVCode")
        self._setstruct(producer,"oref:ClientRegId")
        self._setstruct(producer,"oref:INN")
        self._setstruct(producer,"oref:KPP")
        self._setstruct(producer,"oref:ShortName")

    def _readcontent_InformBReg(self,pos):
        self._setstruct(pos,"wbr:Identity")
        self._setstruct(pos,"wbr:InformBRegId")
        id=self.struct['wbr_Identity']
        del self.struct['wbr_Identity']
        return id
    
    def _read_nattn(self,doc):
        content=doc.find("ttn:ttnlist",ns)
        self.db._truncate(db.TB_EGAIS_DOCS_NEED)
        findtag=("ttn:WbRegID","ttn:ttnNumber","ttn:ttnDate","ttn:Shipper")
        res=0
        for t in content.findall("ttn:NoAnswer",ns):
            struct={}
            for tag in findtag:
                val=t.find(tag,ns)
                if val!=None:
                    struct[tag.replace(":","_")] = val.text
            res+=1
            self.db._insert(db.TB_EGAIS_DOCS_NEED,struct)
        return res

    def _reload_ostat(self,tree):
        products=tree.find("rst:Products",ns)
        if products==None:
            print "no products"
            return
        res=0
        self.db.egais_ostat_clear()
        for t in products.findall("rst:StockPosition",ns):
            n=t.find("rst:Product",ns)
            p=n.find("pref:Producer",ns)
            a=p.find("oref:address",ns)
            struct={}
            for f in self.db.tb_egais_ostat.record_add:
                xf=f.replace("_",":")
                for x in (t,n,p,a):
                    r=x.find(xf,ns)
                    if r!=None:
                        break
                if r!=None:
                    struct[f]=r.text
            res+=1
            #print struct
            self.db.egais_ostat_add(struct)
        return res

    def _addTicket(self,url,reply_id,tree):
        self.struct={}
        id=self._readhead_Ticket(tree)
        if not self.db.egais_find_replyId(reply_id):
            return False
        if self.db.egais_doc[3] == 5:
            return True
        if self.struct.has_key("tc_OperationResult"):
            if self.struct['tc_OperationResult'] == 'Accepted':
                self.struct['status']    = 5
            else:
                self.struct['status']    = 6
        else:
            self.struct['status']    = 4
        self.struct['xml_ticket']= self.data
        self.struct['reply_id']  = reply_id
        self.struct['ns_typedoc']= "Ticket"
        id=self.db.egais_doc[0]
        return self.db.egais_docs_hd_upd(id,self.struct)

    def _addConfirmTicket(self,url,reply_id,tree):
        self.struct={}
        regid=self._readhead_ConfirmTicket(tree)
        if not self.db.egais_find_ttn(regid):
            return False
        if self.struct.has_key("wt_IsConfirm"):
            if self.struct['wt_IsConfirm'] == 'Accepted':
                self.struct['status']    = 5
            else:
                self.struct['status']    = 6
        self.struct['xml_ticket']= self.data
        self.struct['ns_typedoc']= "ConfirmTicket"
        id=self.db.egais_doc[0]
        return self.db.egais_docs_hd_upd(id,self.struct)

    def _addWayBillAct(self,url,reply_id,tree):
        self.struct={}
        regid=self._readhead_WayBillAct(tree)
        if not self.db.egais_find_ttn(regid):
            return False
        if self.struct.has_key("wa_IsAccept"):
            if self.struct['wa_IsAccept'] == 'Accepted':
                self.struct['status']    = 5
            else:
                self.struct['status']    = 6
        self.struct['xml_ticket']= self.data
        self.struct['ns_typedoc']= "WayBillAct_v2"
        self.struct['wt_IsConfirm']=self.struct['wa_IsAccept']
        del self.struct['wa_IsAccept']

        id=self.db.egais_doc[0]
        return self.db.egais_docs_hd_upd(id,self.struct)

    def _addWayBill(self,url,id,tree):
        self.struct={}
        self.struct['type']      = 0
        self.struct['status']    = 0
        self.struct['xml_doc']   = self.data
        self.struct['reply_id']  = id
        self.struct['url']       = url
        self.struct['ns_typedoc']= "WayBill"

        content=self._readhead_WayBill(tree)
        if self.db.egais_docs_find(0,self.struct["recv_RegId"],self.struct["send_RegId"],self.struct["wb_NUMBER"]):
            #Возможно это стоит включить. Если документ приходит с темже номером то он перезаписывается
            #!!! Требует проверки!
            self.db.egais_docs_hd_del(self.db.egais_doc[0])
            if self.db.egais_get_mydoc(self.db.egais_doc[0]):
                return False
        id=self.db.egais_docs_hd_add(self.struct)
        if id==0:
            return False
        for pos in content.findall("wb:Position",ns):
            self.struct={'iddoc':id}
            self._readcontent_WayBill(pos)
            self.struct['real_Quantity']=self.struct['wb_Quantity']
            self.db.egais_docs_ct_add(self.struct)
        return True

    def _addInformBReg(self,url,id,tree):
        self.struct={}
        content=self._readhead_InformBReg(tree)
        if not self.db.egais_find_replyId(id) or id=="":
            print "error:replyid %s" % id
            if not self.db.egais_docs_find(None,self.struct["recv_RegId"],self.struct["send_RegId"],self.struct["wbr_WBNUMBER"]):
                print "not found doc"
                return False
        if self.db.egais_doc[3] not in (0,3,5,6) :
            print "error:doc status=%d" % self.db.egais_doc[3]
            return False
        iddoc=self.db.egais_doc[0]
        tc_regId=self.struct['tc_RegId']
        self.struct={}
        if self.db.egais_doc[3]==0:
            self.struct['status']=1
        if self.db.egais_doc[3]==3:
            self.struct['status']=4
        self.struct['xml_inform']=self.data
        self.struct['url']=url
        #self.struct['reply_id']  = id
        self.struct['ns_typedoc']= "InformBReg"
        self.struct['tc_RegId']=tc_regId
        #print self.struct;
        self.db.egais_docs_hd_upd(iddoc,self.struct)
        for pos in content.findall("wbr:Position",ns):
            self.struct={}
            id=self._readcontent_InformBReg(pos)
            self.db.egais_docs_ct_updId(iddoc,id,self.struct)
        return True

    def _addReplyNoAnswerTTN(self,url,id,tree):
        self.struct={}
        content=self._readhead_InformBReg(tree)

    def _make_act(self,id):
        if not self.db.egais_get_mydoc(id):
            return ""
        xml=XML_SEND_ACT.replace("%fsrar_id%",self.fsrar_id)
        xml=xml.replace("%accept%",self.db.egais_doc_hd['answer'])
        xml=xml.replace("%iddoc%",str(self.db.sets['idplace'])+"_"+self.db.egais_doc_hd['id'])
        xml=xml.replace("%date%",curdate2my())
        xml=xml.replace("%wb_RegId%",self.db.egais_doc_hd['tc_RegId'])
        XML=xml

        XML_CONTENT=""
        use_content=False
        for ct in self.db.egais_doc_ct:
            if ct['real_Quantity']!=ct['wb_Quantity']:
                use_content=True
            xml=XML_ACT_CONTENT.replace("%identity%",ct['wb_Identity'])
            xml=xml.replace("%real%",ct['real_Quantity'])
            xml=xml.replace("%wb_RegId%",str(ct['wbr_InformBRegId']))
            XML_CONTENT+=xml
        if not use_content:
            XML_CONTENT=""
        XML=XML.replace("%content%",XML_CONTENT)
        return XML.encode("utf8")
            
    def _make_return(self,id):
        if not self.db.egais_get_mydoc(id):
            return ""
        xml=XML_SEND_WAYBILL_HEAD.replace("%fsrar_id%",self.fsrar_id)
        rlist={ "%identity%"    :"wb_Identity",\
                "%number%"      :"wb_NUMBER",\
                "%dt%"          :"wb_Date",\
                "%packet%"      :"wb_UnitType",\
                "%inn%"         :"send_INN",\
                "%kpp%"         :"send_KPP",\
                "%regid%"       :"send_RegId",\
                "%name%"        :"send_ShortName",\
                "%send_inn%"    :"recv_INN",\
                "%send_kpp%"    :"recv_KPP",\
                "%send_regid%"  :"recv_RegId",\
                "%send_name%"   :"recv_ShortName",\
               }

        for k,v in rlist.items():
            if v.find('ShortName')!=-1:
                self.db.egais_doc_hd[v]=self.db.egais_doc_hd[v][:64]
            xml=xml.replace(k,self.db.egais_doc_hd[v])
        xml=xml.replace( "%type%","WBReturnFromMe")

        rlist={ "%identity%"    :"wb_Identity",\
                "%quantity%"    :"real_Quantity",\
                "%price%"       :"wb_Price",\
                "%inform_a%"    :"pref_RegId",\
                "%inform_b%"    :"wbr_InformBRegId",\
                "%shortname%"   :"pref_ShortName",\
                "%alccode%"     :"pref_AlcCode",\
                "%capacity%"    :"pref_Capacity",\
                "%alcvolume%"   :"pref_AlcVolume",\
                "%productvcode%":"pref_ProductVCode",\
                "%regid%"       :"oref_ClientRegId",\
                "%inn%"         :"oref_INN",\
                "%kpp%"         :"oref_KPP",\
                "%oref_shortname%"    :"oref_ShortName",\
              }

        XML_CONTENT=""
        for ct in self.db.egais_doc_ct:
            xml2=XML_SEND_WAYBILL_CONTENT

            for k,v in rlist.items():
                if ct[v]!=None and ct[v]!='None':
                    if v=='pref_ShortName':
                        ct[v]=ct[v][:64]
                    xml2=xml2.replace(k,ct[v])
                else:
                    xml2=xml2.replace(k,"None")
                    t=v.replace("_",":")
                    t1="<%s>" % t
                    t2="</%s>" % t
                    xml2=xml2.replace(t1+"None"+t2,"")

            xml2=xml2.replace("%pref_type%",u"АП")
            XML_CONTENT+="\n"+xml2

        XML=xml.replace("%content%",XML_CONTENT)
        return XML.encode("utf8")

    def _make_check(self,_type,ncheck,pos):
        dttm=datetime.now().strftime(format="%d%m%y%H%M")
        xml=XML_CHECK.replace("%inn%",self.db.sets['inn'])
        xml=xml.replace("%kpp%",self.db.sets['kpp'])
        xml=xml.replace("%name%",self.db.sets['orgname'])
        xml=xml.replace("%address%",self.db.sets['placename'])
        xml=xml.replace("%kassa%",self.db.sets['nkassa'])
        xml=xml.replace("%datetime%",dttm)
        xml=xml.replace("%ncheck%",str(ncheck))
        XML=xml
        XML_CONTENT=""
        for i in range(len(pos)):
            p=pos[i]
            if not (p['storno']==0 and p['p_alco']==1):
                continue
            xml=XML_BOTTLE.replace("%barcode%",p['barcode'])
            xml=xml.replace("%ean%",p['p_shk'])
            if p['paramf1']>0 and _type==1:
                price=-p['paramf1']
            else:
                price=p['paramf1']
            xml=xml.replace("%price%",price.__format__(".2f"))
            if p['p_litrag']!=0:
                xml=xml.replace("%litrag%","volume=\"%s\"" % p['p_litrag'].__format__(".4f"))
            else:
                xml=xml.replace("%litrag%","")
            XML_CONTENT+=xml
        XML=XML.replace("%bottles%",XML_CONTENT)
        return XML.encode("utf8")

    def _make_move(self,id):
        if not self.db.egais_get_mydoc(id):
            return ""
        xml=XML_SEND_WAYBILL_HEAD.replace("%fsrar_id%",self.fsrar_id)
        rlist={ "%identity%"    :"wb_Identity",\
                "%number%"      :"wb_NUMBER",\
                "%dt%"          :"wb_Date",\
                "%packet%"      :"wb_UnitType",\
                "%inn%"         :"send_INN",\
                "%kpp%"         :"send_KPP",\
                "%regid%"       :"send_RegId",\
                "%name%"        :"send_ShortName",\
                "%send_inn%"    :"recv_INN",\
                "%send_kpp%"    :"recv_KPP",\
                "%send_regid%"  :"recv_RegId",\
                "%send_name%"   :"recv_ShortName",\
               }

        for k,v in rlist.items():
            if v.find('ShortName')!=-1:
                self.db.egais_doc_hd[v]=self.db.egais_doc_hd[v][:64]
            xml=xml.replace(k,self.db.egais_doc_hd[v])
        xml=xml.replace( "%type%","WBReturnFromMe")

        rlist={ "%identity%"    :"wb_Identity",\
                "%quantity%"    :"real_Quantity",\
                "%price%"       :"wb_Price",\
                "%inform_a%"    :"pref_RegId",\
                "%inform_b%"    :"wbr_InformBRegId",\
                "%shortname%"   :"pref_ShortName",\
                "%alccode%"     :"pref_AlcCode",\
                "%capacity%"    :"pref_Capacity",\
                "%alcvolume%"   :"pref_AlcVolume",\
                "%productvcode%":"pref_ProductVCode",\
                "%regid%"       :"oref_ClientRegId",\
                "%inn%"         :"oref_INN",\
                "%kpp%"         :"oref_KPP",\
                "%oref_shortname%"    :"oref_ShortName",\
              }

        XML_CONTENT=""
        for ct in self.db.egais_doc_ct:
            xml2=XML_SEND_WAYBILL_CONTENT

            for k,v in rlist.items():
                if ct[v]!=None and ct[v]!='None':
                    if v=='pref_ShortName':
                        ct[v]=ct[v][:64]
                    xml2=xml2.replace(k,ct[v])
                else:
                    xml2=xml2.replace(k,"None")
                    t=v.replace("_",":")
                    t1="<%s>" % t
                    t2="</%s>" % t
                    xml2=xml2.replace(t1+"None"+t2,"")

            xml2=xml2.replace("%pref_type%",u"АП")
            XML_CONTENT+="\n"+xml2

        XML=xml.replace("%content%",XML_CONTENT)
        return XML.encode("utf8")

