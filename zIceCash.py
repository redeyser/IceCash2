#!/usr/bin/python
# -*- coding: utf-8
# version 2.000
# Zet for IceCash
"""
    Логика работы с Zet отчетом
"""
import datetime

class zIceCash:
    def __init__(self,db):
        self.db = db

    def _calc(self,full=True,idbegin=None,idend=None):
        self.db.ZetLast=None
        if idbegin==None:
            if self.db._Zet_last():
                idbegin = self.db.ZetLast['end_ncheck']+1
            else:
                idbegin=None
        if not self.db._trsc_calc(idbegin,idend,full=full):
            return False
        if self.db.Zet['c_sale']==0:
            return False
        return True

    def _Z_recalc(self,id):
        self.db._Zet_get(id)
        id0=int(self.db.Zet['begin_ncheck'])
        id1=int(self.db.Zet['end_ncheck'])
        if self._calc(idbegin=id0,idend=id1):
            self.db.Zet['up']=0
            r=self.db._Zet_update(id)
            return r
        else:
            return False

    def _Z(self,idbegin=None,idend=None):
        if self._calc(idbegin=idbegin,idend=idend):
            if self.db.ZetLast!=None:
                number=self.db.ZetLast['number']
            else:
                number=0
            self.db.Zet['number']=number+1
            self.db.Zet['idplace']=self.db.idplace
            self.db.Zet['nkassa']=self.db.nkassa
            r=self.db._Zet_add()
            if r:
                pass
                #Автоматическая выгрузка файла
                #self._get_xml(self.db.ZetID)
                #self._save_xml()
            return r
        else:
            return False

    def _gets(self,cur=True,up=None):
        cur_month_begin=datetime.date.today().replace(day=1)
        cur_month_end=None
        if not cur:
            day=datetime.timedelta(days=1)
            cur_month_end=cur_month_begin-day
            cur_month_begin=cur_month_end.replace(day=1)
        return self.db._Zet_gets(cur_month_begin,cur_month_end,up=up)

    def _get_xml(self,id):
        self.XML_Zet=""
        if not self.db._Zet_get_html(id):
            return False
        head=""
        for k,v in self.db.Zet.items():
            x="<%s>%s</%s>\n" % (k,v,k)
            head+=x

        body=""
        for n in self.db.Zet_ct:
            hline=self.db.tb_Zet_cont.result2values(n)
            sline=""
            for k,v in hline.items():
                sline+="\t<%s>%s</%s>\n" % (k,v,k)
            x="<line>\n%s</line>\n\n" % (sline)
            body+=x

        self.XML_Zet='<?xml version="1.0" encoding="UTF-8"?>\n<data type="icecash_zet">\n\n<head>\n'+head+"</head>\n\n<body>\n"+body+"</body>\n\n</data>"
        return True

    def _save_xml(self):
        path='site/files/upload/'
        idplace=self.db.Zet['idplace']
        nkassa=self.db.Zet['nkassa']
        id=self.db.Zet['id']
        dt=self.db.Zet['date']
        fn=path+"zet_%s_%s_%s_%s.xml" % (idplace,nkassa,id,dt)
        f=open(fn,"w")
        f.write(self.XML_Zet)
        f.close()
        return fn
        




