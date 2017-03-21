#!/usr/bin/python
# -*- coding: utf-8
# version 2.000
# Check logic for IceCash
import math
import my
from  bsIceCash import *
from  prizeIceCash import *
from  clientEgais import *
from actIceCash import *
"""
    Логика работы с чеком
"""
CURR = 0

CH_SALE = 0
CH_RETURN = 1

MULTI_PRICE_NO  = 0
MULTI_PRICE_YES = 1

TRSC_SALE    = 11
TRSC_RETURN  = 13

#users marking position on us_before_calc
MARK_DENY_DISCOUNT  = "#"
MARK_DENY_BONUS     = "*"
MARK_MINPRICE       = "$"
MARK_MAXSKID        = "%"
MARK_ALCO           = "A"

def _round(V,n):
    z=str(V.__format__(".4f")).split(".")
    if len(z)<2:
        return str(V)
    else:
        d=int(z[0])
        f=z[1].ljust(n,"0")
    l=len(f)
    a=[]
    for i in range(l):
        a.append(int(f[i]))
    r=range(l)[n:]
    r.reverse()
    x=range(l)[:n]
    x.reverse()
    ost=0
    for i in r:
        a[i]+=ost
        if a[i]>=5:
            ost=1
        else:
            ost=0
    for i in x:
        a[i]+=ost
        if a[i]>9:
            a[i]=0
            ost=1
        else:
            ost=0
            break
    d+=ost
    s=""
    for i in range(n):
        s+=str(a[i])
    if n>0:
        s="."+s
    result=str(d)+s
    return result

class chIceCash:

    def __init__(self,db,iduser):
        self.iduser = iduser
        self.idcheck=CURR
        self.db = db
        self.actions=Actions(db)
        self.isactions=self.actions._read()

    def _ps_connect(self,idsystem):
        self.ps=prizeIceCash(str(idsystem),self.db.idplace,self.db.nkassa,self.db.sets['backoffice_ip'],int(self.db.sets['prize_port']))
        r=self.ps.connect()
        if r:
            return self.ps.cmd_info()
        return r

    def _ps_gen(self,ncheck,idtrsc,summa):
        if self.ps.cmd_gen(ncheck,idtrsc,summa):
            self.ps.cmd_close()
            self.ps.close();
            return True
        else:
            return False

    def _bs_connect(self):
        self.bs=bsIceCash(self.db.idplace,self.db.nkassa,self.db.sets['backoffice_ip'],int(self.db.sets['bonus_port']))
        return self.bs.connect()

    def _bs_info(self,shk,retry=False):
        result = self.bs.cmd_info(shk)
        #print self.bs.info
        if not result:
            return False
        if int(self.bs.info['type'])==CARD_DISCONT:
            self._sets({"discount_proc":float(self.bs.info['discount'])/100,"discount_card":self.bs.info['id'],"discount_sum":0,'fio':"%s %s %s" % (self.bs.info['name_f'],self.bs.info['name_i'],self.bs.info['name_o'])})
        if int(self.bs.info['type'])==CARD_BONUS:
            if retry:
                self._sets({"bonus_proc":self.bs.info['addproc'],\
                "bonus_card":self.bs.info['id'],\
                "bonus_max":self.bs.info['dedproc'],\
                'bonus_sum':self.bs.info['sum'],\
                'discount_sum':0,\
                'bonus_type':0})
            else:
                self._sets({"bonus_proc":self.bs.info['addproc'],\
                "bonus_card":self.bs.info['id'],\
                "bonus_max":self.bs.info['dedproc'],\
                'bonus_sum':self.bs.info['sum'],\
                'fio':"%s %s %s" % (self.bs.info['name_f'],self.bs.info['name_i'],self.bs.info['name_o']),\
                })
        return True

    def _bs_addsum(self,card,summa,ncheck):
        result = self.bs.cmd_addsum(card,summa,ncheck,0)
        if not result or self.bs.data=="0":
            return False
        else:
            return True

    def _bs_dedsum(self,card,summa,ncheck):
        result = self.bs.cmd_dedsum(card,summa,ncheck,0)
        if not result or self.bs.data=="0":
            return False
        else:
            return True

    def _bs_closesum(self,card):
        result = self.bs.cmd_closesum(card)
        if not result or self.bs.data=="0":
            return False
        else:
            return True

    def _init_dtp(self,dtpclient):
        self.dtpclient=dtpclient

    def _init_egais(self):
        self.egais=EgaisClient(self.db.sets["egais_ip"],8080,self.db)

    def _init_act(self,act):
        self.actions=act

    def _set(self,field,value):
        self.db._check_update(self.iduser,self.idcheck,{field:value})

    def _sets(self,struct):
        self.db._check_update(self.iduser,self.idcheck,struct)

    def _set_type(self,v):
        self._set("type",v)
        self.check_type=v

    def _set_comment(self,v):
        self._set("comment",v)

    def _set_seller(self,v):
        self._set("seller",v)

    def _set_summa(self,v):
        self._set("summa",_round(v,2))

    def _verify_EAN(self,shk):
        if len(shk)<13:
            #return False
            shk=shk.rjust(13,"0")
        s1=0
        for i in range(2,len(shk),2):
            s1+=int(shk[i-1])
        s2=0
        for i in range(1,len(shk),2):
            s2+=int(shk[i-1])
        r=(s1*3+s2)%10
        if r!=0:
            r=10-r
        if r==int(shk[-1]):
            return True
        else:
            #print r,int(shk[-1])
            return False


    def _print_shk(self,id):
        printer=self.db.sets["d_name"]
        if printer=='' or printer=='None':
            return False
        if not self.db._check_pos_get(self.iduser,self.idcheck,id):
            return False
        if self.db.ch_cont_pos["p_shk"]!='':
            self.dtpclient._cm(printer,"prn_lines",{'text':self.db.ch_cont_pos["name"],"width":0,"height":0,"font":1,"bright":10,"big":0})
            return self.dtpclient._cm(printer,"_printcode",{'text':self.db.ch_cont_pos["p_shk"],"width":3,"align":2,"type":2})

    def _add_shk(self,shk,barcode=None):
        if self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        def isprefix(prefix,shk):
            a=prefix.split(";")
            pref=shk[:len(prefix)]
            if pref in a:
                return True
            else:
                return False

        self.findid=None
        self.findtype=None

        if not self._verify_EAN(shk):
            #print "poorshk"
            self.findtype='poor'
            return False

        if isprefix(self.db.sets['scale_prefix'],shk):
            self.findtype='scale'
            code=shk[2:7].lstrip("0")
            count=shk[7:12]
            count=count[0:2]+"."+count[2:]
            #print code,count
            if self._add_tov(code,count,barcode,shk=shk)!=0:
                return True
            else:
                return False

        if isprefix(self.db.sets['user_prefix'],shk):
            self.findtype='user'
            return True
        
        if isprefix(self.db.sets['discount_prefix'],shk):
            self.findtype='discount'
            if self.warning=='true':
                return False
            l=len(self.db.sets['discount_prefix'])
            code=shk[l:-1].lstrip("0")
            if not self.db._discount_get(code):
                return False
            self._set_discount()
            self.db.discount['procent']
            return True

        if isprefix(self.db.sets['bonus_prefix'],shk):
            self.findtype='bonus'
            if self.warning=='true':
                return False
            if not self._bs_connect():
                return False
            if not self._bs_info(shk):
                return False
            return True

        r=self.db._search_shk(shk)
        if r:
            return self._add_tov(self.db.price["id"],1,barcode,shk=shk)
        else:
            return False

    def _chcont_to_pos(self):
        self.pos=[]
        self.isalco=False
        for pos in self.db.ch_cont:
            p=self.db.tb_check_cont.result2values(pos)
            if p['p_alco']==1 and p['storno']==0:
                self.isalco=True
            self.pos.append(p)

    def _pos_upd(self,pos,struct):
        self.db._check_pos_upd(self.iduser,self.idcheck,pos["id"],struct)

    def _pos_read(self):
        self._load_cur()
        self._chcont_to_pos()
        return True

    def _trsc_read(self,id):
        if self.db._trsc_get_check(id,tostr=False):
            self.db.ch_head=self.db.trsc_hd
            self.pos=[]
            for pos in self.db.trsc_ct:
                self.pos.append(pos)
            return True
        else:
            return False

    def _pos_write(self):
        for pos in self.pos:
            self.db._check_pos_upd(self.iduser,self.idcheck,pos["id"],pos)

    def _recalc_pos(self,pos):
        pos["paramf3"]  = float(_round(pos["paramf1"] * pos["paramf2"],2))
        pos["discount"] = 0
        pos["bonus"]    = 0
        return pos

    def _save(self):
        return self.db._check_save(self.iduser)

    def _loadchecks(self,_all):
        return self.db._check_gets(self.iduser,_all)

    def _loadcheck(self,iduser,id):
        if self.db._check_load(iduser,id,self.iduser):
            self._load_cur()
            return True
        else:
            return False

    def _create(self):
        self.check_type=CH_SALE
        self.db._check_create(self.iduser)

    def _print_egais(self):
        printer=self.db.sets["d_name"]
        if printer=='' or printer=='None':
            return False
        if self.db.ch_head.has_key('ncheck'):
            self.ncheck=self.db.ch_head['ncheck']
        else:
            pass
        if self.db.ch_head.has_key('puttime'):
            dt = my.curdate2my()
            tm = my.curtime2my()
        else:
            dt=str(self.db.ch_head['date'])
            tm=str(self.db.ch_head['time'])

        self.dtpclient._cm(printer,"_printsh",{})
        self.dtpclient._cm(printer,"prn_head",{'ncheck':self.ncheck,'dt':dt,'tm':tm})
        self.dtpclient._cm(printer,"prn_qr",{'text':self.db.ch_head['egais_url']})
        self.dtpclient._cm(printer,"_roll",{'count':2})
        self.dtpclient._cm(printer,"prn_lines_def",{'text':self.db.ch_head['egais_url']})
        self.dtpclient._cm(printer,"_roll",{'count':2})
        self.dtpclient._cm(printer,"prn_lines_def",{'text':self.db.ch_head['egais_sign']})
        self.dtpclient._cm(printer,"_roll",{'count':5})
        self.dtpclient._cm(printer,"_cut",{'type':0})
        self.dtpclient._cm(printer,"_printsh",{})
        return True

    def _print_check(self,fiscal,nal,bnal,sdacha,ncheck):
        self.ncheck=ncheck
        printer=self.db.sets["d_name"]
        d_ofd=self.db.sets["d_ofd"]
        if self.db.sets["d_ofd"]=="0":
            ofd=False
        else:
            ofd=True
        if self.db.sets["d_devtype"]=='ESCPOS' or self.db.sets["d_devtype"]=='ESCPOS_OLD':
            escpos=True
        else:
            escpos=False
        _type=self.db.ch_head["type"]
        if _type==0:
            _ctype='sale'
        else:
            _ctype='retsale'
        _discount=self.db.ch_head["discount_sum"]
        _bonus_discount=self.db.ch_head["bonus_discount"]
        _summa=self.db.ch_head["summa"]


        """ ПРИЗОВОЙ ЧЕК ? """
        if self.db.ch_head.has_key("idsystem") and int(self.db.ch_head["idsystem"])!=0:
            _ispriz=True
            _idsystem=self.db.ch_head["idsystem"]
        else:
            _idsystem=0
            _ispriz=False

        if escpos or fiscal==0:
            self.dtpclient._cm(printer,"prn_lines",{'text':self.db.sets["orgname"]+u"\nИНН "+self.db.sets["inn"],"width":0,"height":0,"font":1,"bright":0,"big":0,"invert":0})
            self.dtpclient._cm(printer,"prn_lines",{'text':self.db.sets["placename"]+u"\nКПП "+self.db.sets["kpp"],"width":0,"height":0,"font":1,"bright":10,"big":0,"invert":0})

        """ ОТКРЫТИЕ ЧЕКА """
        if fiscal==1:
            if self.db.sets['d_ncheck']=='1':
                self.dtpclient._cm(printer,"prn_lines",{'text':u"ЧЕК #"+str(ncheck),"width":0,"height":0,"font":1,"bright":10,"big":1,"align":"centers","invert":1})
            else:
                self.dtpclient._cm(printer,"prn_lines",{'text':u"ТОВАРНЫЙ ЧЕК","width":0,"height":0,"font":1,"bright":10,"big":1,"align":"centers","invert":1})
            if not self.dtpclient._cm(printer,"_opencheck",{'type':_ctype}):
                return False
            self.dtpclient._cm(printer,"_openbox",{})
        else:
            self.dtpclient._cm(printer,"prn_lines",{'text':u"КОПИЯ ЧЕКА #"+str(ncheck),"width":0,"height":0,"font":1,"bright":10,"big":1,"invert":1,"align":"centers"})
            self.db.ch_head["bonus_payed"]=1
        if _ctype=='sale':
            _ts=u"ПРОДАЖА\n"
        else:
            _ts=u"ВОЗВРАТ\n"
        self.dtpclient._cm(printer,"prn_lines",{'text':_ts,"width":0,"height":0,"font":1,"bright":10,"big":1,"align":"left","invert":0})

        """ ОБРАБОТКА ПРИЗОВОГО ЧЕКА """
        if _ispriz:
            self.dtpclient._cm(printer,"prn_lines",{'text':u"ЧЕК УЧАВСТВУЕТ В РОЗЫГРЫШЕ!","width":0,"height":0,"font":1,"bright":10,"big":0,"align":"centers","invert":0})
            _err=False
            submessage=u"---"
            self.prize=""
            if int(self.db.ch_head["idprize"])==0:
                if not self._ps_connect(_idsystem):
                    _err=True
                else:
                    if not self._ps_gen(ncheck,0,_summa):
                        _err=True
                if _err:
                    message=u"Призовой сервер недоступен."
                else:
                    self.dtpclient._cm(printer,"prn_lines",{'text':self.ps.info,"width":0,"height":0,"font":3,"bright":1,"big":0,"align":"left","invert":0})
                    if int(self.ps.gen['idprize'])==0:
                        message=u"Ваш чек не выиграл"
                        self._sets({"idprize":-1})
                    else:
                        message=u"Ваш чек выигрышный"
                        self._sets({"idprize":self.ps.gen['idprize']})
                        prize=self.ps.gen['idtov']
                        if int(self.ps.gen['type'])==1:
                            self.prize=prize
                            submessage=u"Ваш приз:\n"+prize+"\n \n"
                        else:
                            submessage=u"Ваш выиигрыш:\nПОДАРОЧНЫЕ ТОВАРЫ В КОНЦЕ ЧЕКА\n \n"
                            t=prize.split(",")
                            for s in t:
                                a=s.split("=")
                                _cp="0"
                                if len(a)==2:
                                    self._add_tov(a[0],a[1],setcur=False,cena=0,root=True)
                                    _cp=a[1]
                                elif len(a)==1:
                                    self._add_tov(a[0],1,setcur=False,cena=0,root=True)
                                    _cp="1"
                                if _cp!="0":
                                    self.prize+=self.db.price["name"]+u" x "+str(_cp)+u"шт<br>"
                                    
                            self._pos_read()
            else:
                message=u"Ваш чек уже розыгрывался"
                submessage=u"ВАШ ВЫИГРЫШ ПОД КОДОМ: [%s]" % self.db.ch_head["idprize"]

            self.dtpclient._cm(printer,"prn_lines",{'text':message,"width":0,"height":1,"font":1,"bright":0,"big":0,"align":"centers","invert":0})
            self.dtpclient._cm(printer,"prn_lines",{'text':submessage+u" \n","width":0,"height":0,"font":1,"bright":10,"big":0,"align":"centers","invert":0})

        """ ПЕЧАТЬ ПОЗИЦИЙ ЧЕКА """
        for p in range(len(self.pos)):
            pos=self.pos[p]
            if pos['storno']==1:
                continue


            """ Печать строки для штриха или для старого варианта или если это копия чека """
            if not ofd or self.db.sets['d_devtype']=='KKM_SHTRIHM' or fiscal==0:
                self.dtpclient._cm(printer,"prn_lines",{'text':pos['name'],"width":0,"height":0,"font":1,"bright":10,"big":0,"align":"left","invert":0})
            
            """ Изменение цены. скидку вкручиваем в цену. Так требует ОФД """
            if pos['discount']>0 or pos['bonus_discount']>0:
                _cena=_round((pos['paramf3']-pos['discount']-pos['bonus_discount'])/pos['paramf2'],2)
            else:
                _cena=_round(pos['paramf1'],2)
            
            if not self.dtpclient._cm(printer,"prn_sale_short",\
                    {   'fiscal'    : fiscal,\
                        'oper'      : _ctype,\
                        'title'     : pos['name'],\
                        'section'   : pos['p_section'],\
                        'realcena'  : _cena,\
                        'p1'        : _round(pos['paramf1'],2),\
                        'p2'        : _round(pos['paramf2'],3),\
                        'p3'        : _round(pos['paramf3'],2),\
                        'ch'        : ' ',\
                        'bonus'     : _round(pos['bonus'],2),\
                        'discount'  : _round(pos['discount']+pos['bonus_discount'],2),\
                        'line'      : '~',
                        'ofd'       : d_ofd }):
                return False

        #self.dtpclient._cm(printer,"_discount",{'islast':0,'issum':1,'isgrow':0,'summa':_round(1,2)})
        
        #""" ПОДЫТОГ """
        #if not self.dtpclient._cm(printer,"_preitog",{}):
        #    return False
        

        #""" ПРОВЕДЕНИЕ СУММОВОЙ СКИДКИ НА ВЕСЬ ЧЕК """
        #if (not escpos)and(fiscal==1)and(_discount+_bonus_discount)>0:
        #    if not self.dtpclient._cm(printer,"_discount",{'islast':0,'issum':1,'isgrow':0,'summa':_round(_discount+_bonus_discount,2)}):
        #        return False

        """ ДИСКОНТНАЯ КАРТА """
        if self.db.ch_head["discount_card"]!="":
            self.dtpclient._cm(printer,"prn_lines",{'text':u"*** Дисконтная карта #"+self.db.ch_head["discount_card"],"width":0,"height":0,"font":1,"bright":10,"big":0})
            self.dtpclient._cm(printer,"prn_lines",{'text':u"*** Процент скидки: "+_round(self.db.ch_head["discount_proc"]*100,2)+u"%","width":0,"height":0,"font":1,"bright":10,"big":0})
            self.dtpclient._cm(printer,"prn_line",{'ch':"="})

        """ БОНУСНАЯ ВСТАВКА """
        if self.db.ch_head["bonus_card"]!="" and self.db.ch_head["bonus_payed"]!=2:
            if fiscal==1:
                if not self._bs_connect():
                    self.dtpclient.result_name=u":Нет связи с бонусной системой"
                    self._sets({"errors":"bs"})
                    return False
                if not self._bs_info(self.db.ch_head["bonus_card"],retry=False):
                    self.dtpclient.result_name=u":Нет связи с бонусной системой"
                    self._sets({"errors":"bs"})
                    return False

                self.dtpclient._cm(printer,"prn_lines",{'text':u"*** Бонусная карта #"+self.bs.info["id"],"width":0,"height":0,"font":1,"bright":10,"big":0})
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Процент начисления:","value":_round(float(self.bs.info["addproc"])*100,2)+u"%","ch":" "})
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Процент списания:","value":_round(float(self.bs.info["dedproc"])*100,2)+u"%","ch":" "})
                _bonus=float(self.db.ch_head["bonus"])
                _bonus_sum=float(self.bs.info["sum"])
                _bonus_discount2=_bonus_discount
                _bonus2=0

                if self.db.ch_head["bonus_payed"]==0 and _bonus_discount>0:
                    if _ctype=='sale':
                        if not self._bs_dedsum(self.db.ch_head["bonus_card"],_round(_bonus_discount,2),ncheck):
                            self.dtpclient.result_name=u":Отказ бонусной операции"
                            return False
                        if abs(abs(float(self.bs.data))-_bonus_discount)>1:
                            self.dtpclient.result_name=u":Сервер скорректировал сумму списания"
                            return False
                    else:
                        if not self._bs_addsum(self.db.ch_head["bonus_card"],_round(_bonus_discount,2),ncheck):
                            self.dtpclient.result_name=u":Отказ бонусной операции"
                            return False
                        _bonus_discount2=-_bonus_discount

                    if not self._bs_closesum(self.db.ch_head["bonus_card"]):
                        self.dtpclient.result_name=u":Отказ закрытия бонусных списаний"
                        return False

                    self._sets({"bonus_payed":1,"ro":1})

                if self.db.ch_head["bonus_payed"]!=2 and _bonus>0:
                    if _ctype=='sale':
                        if not self._bs_addsum(self.db.ch_head["bonus_card"],_round(_bonus,2),ncheck):
                            self.dtpclient.result_name=u":Отказ бонусной операции"
                            return False
                        _bonus2=_bonus
                    else:
                        if not self._bs_dedsum(self.db.ch_head["bonus_card"],_round(_bonus,2),ncheck):
                            self.dtpclient.result_name=u":Отказ бонусной операции"
                            return False
                        _bonus2=-_bonus

                    if not self._bs_closesum(self.db.ch_head["bonus_card"]):
                        self.dtpclient.result_name=u":Отказ закрытия бонусных начислений"
                        return False

                    self._sets({"bonus_payed":2,"ro":1})

                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Начальный остаток",'value':_round(_bonus_sum,2),'ch':"."})
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Начислено бонусов",'value':_round(_bonus2,2),'ch':"."})
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Списано бонусов",'value':_round(_bonus_discount2,2),'ch':"."})
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Конечный остаток",'value':_round(_bonus_sum+_bonus2-_bonus_discount2,2),'ch':"."})
                self.dtpclient._cm(printer,"prn_line",{'ch':"="})
                self.bs.close()

            else:
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Начислено бонусов",'value':_round(self.db.ch_head["bonus"],2),'ch':"."})
                self.dtpclient._cm(printer,"prn_sale_style",{'text':u"*** Списано бонусов",'value':  _round(self.db.ch_head["bonus_discount"],2),'ch':"."})
                self.dtpclient._cm(printer,"prn_line",{'ch':"="})
                

        """ ПРИВЕДЕНИЕ КОМПЛЕКСНОЙ ОПЛАТЫ К ОДНОМУ ТИПУ"""
        if self.db.sets['d_devtype']=='KKM_FPRINT':
            if nal==0 and bnal>0:
                _type_pay=2
            else:
                _type_pay=1
                nal=nal+bnal
                bnal=0

        if _ctype=='sale':
            _summa_pay=_round(nal,2)
        else:
            _summa_pay=0

        #self.dtpclient.result_name=u":Всему пиздец"
        #return False

        """ НЕ ФИСКАЛЬНАЯ ПЕЧАТЬ ИТОГОВ """
        if (fiscal==0)or(escpos):
            sdacha=_round(nal-(_summa-_discount-_bonus_discount),2)
            self.dtpclient._cm(printer,"prn_sale_itog",{'vsego':_round(_summa,2),\
            'discount':_round(self.db.ch_head["discount_sum"]+self.db.ch_head["bonus_discount"],2),\
            'itogo':_round(_summa-_discount-_bonus_discount,2),'nal':_summa_pay,'bnal':_round(bnal,2),'sdacha':sdacha,'ch':" "})
            if fiscal==1:
                self.db.ch_head['date']=my.curdate2my()
                self.db.ch_head['time']=my.curtime2my()
            self.dtpclient._cm(printer,"prn_head",{'ncheck':ncheck,'dt':self.db.ch_head['date'],'tm':self.db.ch_head['time']})
            if not escpos:
                self.dtpclient._cm(printer,"_roll",{'count':5})
            self.dtpclient._cm(printer,"_printsh",{})
            self.dtpclient._cm(printer,"_cut",{'type':1})
            return True

        """ ЗАКРЫТИЕ ЧЕКА """
        if self.db.sets['d_devtype']=='KKM_FPRINT':
            if not self.dtpclient._cm(printer,"_closecheck",{'type':_type_pay,'summa':_summa_pay}):
                self._sets({"ro":1,"errors":"#"})
                return False
        else:
            if not self.dtpclient._cm(printer,"_closecheck",{'nal':_round(nal,2),'bnal':_round(bnal,2)}):
                self._sets({"ro":1,"errors":"#"})
                return False

        self.dtpclient._cm(printer,"_beep",{})

        return True

    def _send_egais(self,_type,ncheck):
        self._init_egais()
        if self.egais._send_check(_type,ncheck,self.pos):
            print "xml sended"
            print self.egais.data
            print self.egais.url
            print self.egais.sign
            self._sets({"egais_xml":self.egais.data,"egais_url":self.egais.url,"egais_sign":self.egais.sign,'ro':1})
            self.db.ch_head['egais_url']=self.egais.url
            self.db.ch_head['egais_sign']=self.egais.sign
            return True
        else:
            self._sets({"errors":"E","egais_xml":self.egais.data})
            print "error xml ticket"
            print self.egais.data
            return False

    def _copycheck(self,id):
        self._trsc_read(id)
        if not self._print_check(0,self.db.ch_head['pay_nal'],self.db.ch_head['pay_bnal'],0,self.db.ch_head['ncheck']):
            self.error=self.dtpclient.result_name
            return False
        else:
            if self.db.ch_head["egais_sign"]!='':
                self._print_egais()
            return True

    def _pay(self,ncheck,nal,bnal):
        self.error="0"
        self.prize=""
        self._calc()
        self._pos_read()
        self.sdacha=0
        if len(self.db.ch_cont)==0:
            self.error=u":Попытка олатить пустой чек"
            return False
        _discount=self.db.ch_head["discount_sum"]
        _bonus_discount=self.db.ch_head["bonus_discount"]
        _summa=self.db.ch_head["summa"]
        _type=self.db.ch_head["type"]
        if _type==0:
            self.sdacha=float(_round(nal+bnal-(_summa-_discount-_bonus_discount),2))
            n=nal-self.sdacha
            if n<0:
                nal=0
                bnal=bnal-nal
                self.sdacha=0
        else:
            self.sdacha=float(_round((_summa-_discount-_bonus_discount)+nal+bnal,2))
        if self.sdacha<0:
            self.error="-1"
            return False
        if self.isalco and self.db.ch_head["egais_sign"]=='':
            if not self._send_egais(_type,ncheck):
                self.error="-2"
                return False
        try:
            if not self._print_check(1,nal,bnal,self.sdacha,ncheck):
                self.error=self.dtpclient.result_name
                return False
        except:
            self.error=u":Ошибка процессинга"
            return False

        if self.isalco:
            try:
                self._print_egais()
            except:
                pass

        if self.db.sets["d_name"]=='None':
            isfiscal=0
        else:
            isfiscal=1
        self.db._check_to_trsc(ncheck,nal,bnal,1,isfiscal)
        self.db._check_delete(self.iduser,0)
        return True
            
    def _before_calc(self):
        if self.isactions:
            return self.actions._do_before_calc(self)
        return True
            
    def _after_calc(self):
        if self.isactions:
            return self.actions._do_after_calc(self)
        return True

    def _calc(self):
        self._docalc()
        if self.check_type!=CH_SALE:
            return
        if self._before_calc():
            self._docalc()
        self._after_calc()

    def _docalc(self):
        def calc_discount(cena,count,proc,_minprice):
            summa = float(_round(cena*count,2))
            _cena = float(_round(cena*(1-proc),2))
            _cena = _minprice if _cena<_minprice else _cena
            _summa = float(_round(_cena*count,2))
            discount = summa - _summa
            return (_cena, discount)

        def getvars(pos):
            if pos['p_max_skid']!=0:
                minp = pos['p_cena']-pos['p_cena']*(pos['p_max_skid']/100)
            else:
                minp = 0

            if pos['p_minprice']!=0:
                if minp>pos['p_minprice']:
                    minp=pos['p_minprice']

            return  (minp,\
            pos['p_max_skid'],\
            pos['paramf1'],\
            pos['paramf2'],\
            pos['paramf3'],\
            pos['mark'],\
            pos['dcount'],\
            pos['discount'],\
            pos['bonus_discount'],\
            pos['discount_pos'],\
            pos['bonus_pos'],\
            )

        def getcard():
            if self.db.ch_head["discount_card"]!="":
                _discount_card=True
                try:
                    _real = int(self.db.ch_head["discount_card"])
                    _real = True
                except:
                    _real=False
            else:
                _discount_card=False
                _real=False


            if self.db.ch_head["bonus_card"]!="":
                _bonus_card=True
            else:
                _bonus_card=False
            return (_discount_card,_bonus_card,_real)

        """ Читаем чек """
        self._pos_read()
        self.us_before_calc()

        sumcheck=0
        discount=0
        discount_bonus=0
        bonus=0

        _type=self.db.ch_head["type"]
        ds=self.db.ch_head["discount_sum"]
        db=self.db.ch_head["bonus_discount"]
        dp=self.db.ch_head["discount_proc"]
        bp=self.db.ch_head["bonus_proc"]
        bm=self.db.ch_head["bonus_max"]
        bs=self.db.ch_head["bonus_sum"]
        bt=self.db.ch_head["bonus_type"]
        cursor=self.db.ch_head["cursor"]
        iscursor=False

        (_discount_card,_bonus_card,_real_card)=getcard()

        """ Обычный пересчет позиций и накопление суммы чека """
        for p in range(len(self.pos)):
            pos=self.pos[p]
            if pos['storno']!=1:
                pos=self.us_before_calc_pos(pos)
                pos=self._recalc_pos(pos)
                self.pos[p]=pos
                sumcheck+=pos['paramf3']
            if pos['id']==cursor:
                iscursor=True

        """ Расчет скидки по позициям
            discount - по дисконтной карте
            bonus - по бонусной (максимально возможная)
        """
        for p in range(len(self.pos)):
            pos=self.pos[p]
            dsum=0
            bsum=0

            if pos['storno']!=1:
                (_minprice, _maxskid, _cena, _count, _summa, _mark, _dcount,_discount,_discount_bonus,_discount_pos,_bonus_pos) = getvars(pos)

                if _dcount==None:
                    _dcount=_count

                """ Установка позиционного процента скидки, если он больше общего """
                if _discount_pos>dp:
                    _dp=_discount_pos
                else:
                    _dp=dp

                """ Высчитываем процентную скидку и новую цену """
                if _discount_card and _mark.find(MARK_DENY_DISCOUNT)==-1:
                    (_cena,dsum) = calc_discount(_cena,_dcount,_dp,_minprice)
                """ Высчитываем максимально возможное списание бонусами, исходя из скидочной цены """
                if _bonus_card and bt==1 and _mark.find(MARK_DENY_DISCOUNT)==-1:
                    (_cena,bsum) = calc_discount(_cena,_count,bm,_minprice)
                
                #print "calc_discount:",_cena,_count,_summa,dsum
                discount+=dsum
                discount_bonus+=bsum

            pos['discount']=dsum
            pos['bonus_discount']=bsum
            self.pos[p]=pos

        cur_discount=discount_bonus

        """ Если есть списание по бонусам, то корректируем его,
            в случае если накопления по карте меньше макимально возможной скидки
        """
        if _bonus_card and bt==1 and _type==0:
            """ Если выставлено списание вручную, то снижаем скидку """
            if db>0 and db<discount_bonus:
                cur_discount=db
            else:
                cur_discount=discount_bonus
            """ Если текущая скидка меньше максимально расчетной
                или больше накоплений, то корректируем скидку впозициях
            """
            if cur_discount<discount_bonus or cur_discount>bs:
                """ Корректировочный коэфицент будет всегда понижающим """
                if cur_discount<discount_bonus:
                    p_correct=cur_discount/discount_bonus
                else:
                    p_correct=bs/cur_discount
                    cur_discount=bs

                discount_bonus=0
                for p in range(len(self.pos)):
                    pos=self.pos[p]
                    bsum=0
                    if pos['storno']!=1:
                        bsum=float(_round(pos["bonus_discount"]*p_correct,2))
                        discount_bonus+=bsum
                    pos['bonus_discount']=bsum
                    self.pos[p]=pos
                    
            discount_bonus=cur_discount

        """ Пересчитываем скидку и списание бонусов
            Таким образом, чтобы позиционные суммы оказались
            кратными округленным скидочным ценам 
            А также суммируем все откорректированные скидки
        """
        discount=0
        discount_bonus=0
        for p in range(len(self.pos)):
            pos=self.pos[p]
            if pos['storno']!=1:
                _summa=pos["paramf3"]
                _count=pos["paramf2"]
                dsum=pos["discount"]
                bsum=pos["bonus_discount"]
                """ Высчитываем цену после двух скидок и корректируем суммы скидок"""
                _cena = float(_round((_summa-dsum-bsum)/_count, 2))
                _nsumma=float(_round(_cena*_count,2))
                delta = (_summa-_nsumma)-(dsum+bsum)
                #print "delta:",delta,_summa,_cena,_count,dsum,bsum
                if dsum>0:
                    dsum+=delta
                else:
                    bsum+=delta
                pos["discount"]=dsum
                pos["bonus_discount"]=bsum
                discount+=dsum
                discount_bonus+=bsum
                pos["bonus"]=0
                self.pos[p]=pos

        """ В результате округлений, сумма списания бонусов
            может оказаться немного больше суммы накоплений
            Бонусный сервер должен допускать списание в минул
            на копеечные суммы
        """

        """ Последний этап, это начисление бонусов 
            Бонусы начисляются только если не было скидки по дисконтной карте
        """
        if _bonus_card and not _real_card:
            for p in range(len(self.pos)):
                pos=self.pos[p]
                bsum=0
                if pos['storno']!=1:
                    (_minprice, _maxskid, _cena, _count, _summa, _mark, _dcount,_discount,_discount_bonus,_discount_pos,_bonus_pos) = getvars(pos)

                    """ Установка позиционного процента бонуса, если он больше общего """
                    if _bonus_pos!=bp and _bonus_pos!=0:
                        _bp=_bonus_pos
                    else:
                        _bp=bp

                    if _discount==0:
                        if (_discount>0)or(_discount_bonus>0):
                            """ Расчитываем фактическую цену если была скидка """
                            _cena=float(_round((_summa-_discount-_discount_bonus)/_count,2))
                        
                        if _dcount==None:
                            _dcount=_count
                        
                        if _mark.find(MARK_DENY_BONUS)==-1: 
                            (_cena,bsum) = calc_discount(_cena,_dcount,_bp,_minprice)
                        else:
                            bsum=0

                    bonus+=bsum

                pos['bonus']=bsum
                self.pos[p]=pos

        """ Записываем изменения в чек """
        self._pos_write()
        self._sets({"bonus":bonus,"discount_sum":discount,"bonus_discount":discount_bonus,"summa":sumcheck})
        if not iscursor and cursor!=0:
            self._set("cursor",self.pos[0]['id'])

    def _set_discount(self):
        if self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        if self.db.discount==None:
            return False
        self._sets({"discount_proc":self.db.discount['procent'],"discount_card":self.db.discount['number'],"discount_sum":0})
        self._calc()

    def _add_tov(self,code,count=1,barcode=None,setcur=True,shk='',cena=None,root=False):
        if not root and self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        if not self.db._price_get(code=code):
            return 0
        if self.db.price['istov']==0:
            return 0
        if self.db.price['alco']==1:
            tm=time.localtime()
            if (tm.tm_hour*60+tm.tm_min)>(22*60+57) or tm.tm_hour<8:
                return -3
            if barcode==None:
                return -1
            if self.db._check_pos_barcode(self.iduser,self.idcheck,barcode):
                return -2
        if shk=='':
            shk='-'
        id=self.db._check_pos_add(\
        self.iduser,self.idcheck,\
          {\
            "code"      :code,\
            "paramf2"   :count,\
            "barcode"   :barcode,\
            "p_shk"     :shk,\
          }\
        )
        shcode=False
        if not root:
            self._sets({"discount_sum":0,'bonus_discount':0})

        self.db._check_pos_info_set(self.iduser,self.idcheck,id,shcode=shcode,cena=cena)
        self.us_after_add_tov(id,code)
        if setcur:
            self._set("cursor",id)
        return id

    def us_after_add_tov(self,id,code):
        pass


    def us_before_calc(self):
        pass

    def us_before_calc_pos(self,pos):
        #marking position as deny discount and bonus for section=2
        def addp(p,c):
            if p['mark'].find(c)==-1:
                p['mark']+=c
        try:
            if pos['p_alco']!=0:
                addp(pos,MARK_ALCO)
            if pos['p_minprice']!=0 or pos['p_maxprice']!=0:
                addp(pos,MARK_MINPRICE)
            if pos['p_max_skid']!=0:
                addp(pos,MARK_MAXSKID)
            if pos['p_section'] in [2]:
                addp(pos,MARK_DENY_BONUS)
            if pos['p_section'] in [3]:
                addp(pos,MARK_DENY_DISCOUNT)
        except:
            pass
        finally:
            return pos

    def _selprice(self,id):
        if not self.db._check_pos_get(self.iduser,self.idcheck,id):
            return False
        if self.db.ch_cont_pos["multiprice"]==0:
            return False
        if not self.db._price_get(code=self.db.ch_cont_pos["code"]):
            return False
        return True

    def _setprice(self,id,cena):
        if self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        if not self._selprice(id):
            return False

        result=False
        for d in self.db.price_shk:
            if cena=="%.2f" % d[3]:
                result=True
                self._pos_upd(self.db.ch_cont_pos,{"paramf1":cena})
                break
        return result

    def _chprice(self,id,val):
        if self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        if not self.db._check_pos_get(self.iduser,self.idcheck,id):
            return False

        if self.db.ch_cont_pos["p_minprice"]==0:
            self.db.ch_cont_pos["p_minprice"]=self.db.ch_cont_pos["p_cena"]
        if self.db.ch_cont_pos["p_maxprice"]==0:
            self.db.ch_cont_pos["p_maxprice"]=self.db.ch_cont_pos["p_cena"]
        mark=self.db.ch_cont_pos["mark"]+"p"

        if val<=self.db.ch_cont_pos["p_maxprice"] and val>=self.db.ch_cont_pos["p_minprice"]:
            self._pos_upd(self.db.ch_cont_pos,{"paramf1":val,'mark':mark})
        else:
            return False
        self._sets({"discount_sum":0,'bonus_discount':0})
        return True

    def _chskid(self,id,proc):
        if self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        if not self.db._check_pos_get(self.iduser,self.idcheck,id):
            return False
        if self.db.ch_cont_pos["p_max_skid"]<proc:
            return False

        cena=_round(self.db.ch_cont_pos["p_cena"]-self.db.ch_cont_pos["p_cena"]*(proc/100),2)
        mark=self.db.ch_cont_pos["mark"]+"s"

        if cena>=self.db.ch_cont_pos["p_minprice"]:
            self._pos_upd(self.db.ch_cont_pos,{"paramf1":cena,'mark':mark})
        else:
            return False
        self._sets({"discount_sum":0,'bonus_discount':0})
        return True

    def _chcount(self,id,val):
        if val==0:
            return False
        if self.db._check_hd_get(self.iduser,self.idcheck):
            if self.db.ch_head['ro']!=0:
                return False
        if not self.db._check_pos_get(self.iduser,self.idcheck,id):
            return False
        if not val.is_integer() and self.db.ch_cont_pos["p_real"]==0:
            return False
        if self.db.ch_cont_pos["p_alco"]==1:
            return False

        mark=self.db.ch_cont_pos["mark"]+"+"

        self._pos_upd(self.db.ch_cont_pos,{"paramf2":val,'mark':mark})
        self._sets({"discount_sum":0,'bonus_discount':0})
        return True

    def _storno(self,id):
        if not self.db._check_pos_get(self.iduser,self.idcheck,id):
            return False
        if self.db.ch_cont_pos["storno"]==0:
            v=1
        else:
            v=0
        mark=self.db.ch_cont_pos["mark"]+"c"
        self._pos_upd(self.db.ch_cont_pos,{"storno":v,'mark':mark})
        self._sets({"discount_sum":0,'bonus_discount':0})
        #self._set("cursor",id)

    def _cancel(self,ncheck):
        self._load_cur()
        if len(self.db.ch_cont)==0:
            self.db._check_delete(self.iduser,0)
            self._create()
            return True
        if self.db.ch_head['bonus_payed']!=0 or self.db.ch_head['egais_sign']!='':
            self._save()
            return True
        self.db._check_to_trsc(ncheck,0,0,0,0)
        self.db._check_delete(self.iduser,0)
        self._create()
        return True

        if self.db.ch_head['bonus_payed']!=0:
            return False

    def _load(self,idcheck):
        result = self.db._check_get(self.iduser,idcheck)
        if result:
            self.idcheck=idcheck
            if self.db.ch_head["cursor"]==0 or len(self.db.ch_cont)==0:
                self.db.ch_head["cursor"]=len(self.db.ch_cont)
            self.check_type=self.db.ch_head["type"]
        else:
            self.idcheck=CURR
            self.check_type=CH_SALE
        return result


    def _load_cur(self):
        if not self._load(CURR):
            self._create()
            self._load(CURR)


