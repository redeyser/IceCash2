#!/usr/bin/python
# -*- coding: utf-8
# version 2.000
# DataBase for IceCash
import my
import os
import re
from chIceCash import _round
from md5 import md5
import tbIceCash as tbs
import datetime

DATABASE = "IceCash"
MYSQL_USER = "icecash"
MYSQL_PASSWORD = "icecash1024"
TB_BOXES_HD  = "tb_boxes_hd"
TB_BOXES_CT  = "tb_boxes_ct"
TB_CHECK_HEAD = "tb_check_head"
TB_CHECK_CONT = "tb_check_cont"
TB_EGAIS_PLACES = "tb_egais_places"
TB_EGAIS_OSTAT  = "tb_egais_ostat"
TB_EGAIS_DOCS_HD  = "tb_egais_docs_hd"
TB_EGAIS_DOCS_CT  = "tb_egais_docs_ct"
TB_EGAIS_DOCS_NEED  = "tb_egais_docs_need"

SPEED = {\
    1:1200,\
    2:2400,\
    3:4800,\
    4:9600,\
    5:14400,\
    6:38400,\
    7:57600,\
    8:115200\
}

TYPE_USER = {\
    "ADMIN"     :100,\
    "KASSIR"    :50,\
    "SELLER"    :10,\
}

def Str2Shash(s,c,eq):
    a = s.split(c)
    Sarr=[]
    for e in a:
        Sarr.append(e.strip(" "))
    Shash={}
    for e in Sarr:
        if e.find(eq)!=-1:
            a=e.split(eq)
            Shash[a[0].strip(" ")] = a[1].strip(" ")
        else:
            Shash[e.strip(" ")] = e.strip(" ")
    return Shash

def array4json(a):
    r=[]
    for h in a:
        if type(h)==datetime.timedelta or type(h)==datetime.date:
            r.append(str(h))
        else:
            r.append(h)
    return r

class dbIceCash(my.db):
    def __init__(self,dbname,host,user,password):
        self.tbs={}
        my.db.__init__(self,dbname,host,user,password)
        self.tb_sets        = tbs.tb_sets       ('tb_sets')
        self.tb_price       = tbs.tb_price      ('tb_price')
        self.tb_price_shk   = tbs.tb_price_shk  ('tb_price_shk')
        self.tb_discount    = tbs.tb_discount   ('tb_discount')
        self.tb_users       = tbs.tb_users      ('tb_users')
        self.tb_trsc_hd     = tbs.tb_trsc_hd    ('tb_trsc_hd')
        self.tb_trsc_ct     = tbs.tb_trsc_ct    ('tb_trsc_ct')
        self.tb_check_head  = tbs.tb_check_head ('tb_check_head')
        self.tb_check_cont  = tbs.tb_check_cont ('tb_check_cont')
        self.tb_types       = tbs.tb_types      ('tb_types')
        self.tb_Zet         = tbs.tb_Zet        ('tb_Zet')
        self.tb_Zet_cont    = tbs.tb_Zet_cont   ('tb_Zet_cont')
        self.tb_egais_places  = tbs.tb_egais_places  ('tb_egais_places')
        self.tb_egais_docs_hd = tbs.tb_egais_docs_hd ('tb_egais_docs_hd')
        self.tb_egais_docs_ct = tbs.tb_egais_docs_ct ('tb_egais_docs_ct')
        self.tb_egais_ostat   = tbs.tb_egais_ostat   ('tb_egais_ostat')
        self.tb_actions_hd    = tbs.tb_actions_hd ('tb_actions_hd')
        self.tb_tlist         = tbs.tb_tlist ('tb_tlist')
        self.tb_egais_docs_need = tbs.tb_egais_docs_need ('tb_egais_docs_need')
        self._tbinit(TB_BOXES_HD)
        self._tbinit(TB_BOXES_CT)
        self._tbinit(TB_CHECK_HEAD)
        self._tbinit(TB_CHECK_CONT)
        self._tbinit(TB_EGAIS_PLACES)
        self._tbinit(TB_EGAIS_OSTAT)
        self._tbinit(TB_EGAIS_DOCS_HD)
        self._tbinit(TB_EGAIS_DOCS_CT)
        self._tbinit(TB_EGAIS_DOCS_NEED)

    def _tbinit(self,name):
        tb=getattr(tbs, name)
        self.tbs[name] = tb(name)

    def _tbcreate(self,tn):
        self.run(self.tbs[tn]._create())

    def _recreate(self):
        for name in self.tbs.keys():
            if not name in self.tables:
               self._tbcreate(name)
               print "created table %s" % name

    def _tables(self):
        res=self.get("show tables")
        db=[]
        for r in res:
            db.append(r[0])
        self.tables=db

    def truncate_trsc(self):
        self.run("truncate tb_Zet")
        self.run("truncate tb_Zet_cont")
        self.run("truncate tb_trsc_hd")
        self.run("truncate tb_trsc_ct")
        self.run("truncate tb_actions_hd")
        self.run("truncate tb_tlist")
        self.run("truncate tb_check_head")
        self.run("truncate tb_check_cont")
        return True

    def truncate_egais(self):
        self.run("truncate tb_egais_docs_hd")
        self.run("truncate tb_egais_docs_ct")
        self.run("truncate tb_egais_places")
        self.run("truncate tb_egais_ostat")
        return True

    """ Optimize functions ----------------------- """

    def _gets(self,tn,tostr=False,dttm2str=True):
        self.result_order=[]
        result = self.get(self.tbs[tn]._gets())
        if len(result)==0:
            return None
        else:
            res=[]
            for r in result:
                res.append(self.tbs[tn].result2values(r,tostr=tostr,dttm2str=dttm2str))
            return res

    """ Получить запись по id """
    def _getid(self,tn,id,tostr=False,dttm2str=True):
        res = self.get(self.tbs[tn]._getid(id))
        if len(res)==0:
            return None
        else:
            return self.tbs[tn].result2values(res[0],tostr=tostr,dttm2str=dttm2str)

    """ Получить записи по idhd """
    def _gethd(self,tn,id,tostr=False,dttm2str=True):
        res = self.get(self.tbs[tn]._gethd(id))
        if len(res)==0:
            return []
        else:
            result=[]
            for r in res:
                result.append( self.tbs[tn].result2values(r,tostr=tostr,dttm2str=dttm2str) )
        return result

    """ Получить Заголовочную запись и подчиненные """
    def _get_data_hd_ct(self,tb_hd,tb_ct,id,tostr=False,dttm2str=True):
        hd = self._getid(tb_hd,id,tostr=tostr,dttm2str=dttm2str)
        if hd != None:
            ct = self._gethd( tb_ct,id,tostr=tostr,dttm2str=dttm2str ) 
        else:
            ct=None
        return (hd,ct)

    """ Очистить таблицу """    
    def _truncate(self,tn):
        self.run("truncate %s" % tn)
        return True

    """ Переделать в хэш """
    def _db2hash(self,r,id,val):
        h={}
        for rec in r:
            h[rec[id]]=rec[val]
        return h

    """ Переделать в массив """
    def _db2arr(self,r,id):
        t=[]
        for rec in r:
            t.append(rec[id])
        return t

    """ Простая выборка """
    def _select(self,tn,where="",fields=None,order=None,group=None,tostr=False,dttm2str=True,toarr=False,tohash=False,nofields=False):
        self.result_order=[]
        if where!="" and fields==None:
            where= " where %s" % where
        if group:
            _group=" group by "+group
        else:
            _group=""
        if order:
            _order=" order by "+order
        else:
            _order=""
        if fields==None:
            result = self.get(self.tbs[tn].query_all_select()+where+_group+_order)
        else:
            result = self.get(self.tbs[tn].query_select(fields,where)+_group+_order)
        if len(result)==0:
            return []
        else:
            if toarr:
                res=[]
                for r in result:
                    if tostr:
                        s=str(r[0])
                    else:
                        s=r[0]
                    res.append(s)
                return res
            if tohash:
                res={}
                self.result_order=[]
                for r in result:
                    if tostr:
                        s=str(r[1])
                    else:
                        s=r[1]
                    res[r[0]]=s
                    self.result_order.append(r[0])
                return res
            res=[]
            if not nofields:
                for r in result:
                    res.append(self.tbs[tn].result2values(r,tostr=tostr,dttm2str=dttm2str))
            else:
                res=result
            return res

    """ Добавить запись """
    def _insert(self,tn,struct):
        r=self.run(self.tbs[tn].query_insert(struct))
        if not r:
            self.lastid=0
            return False
        self.lastid=self.get(my.Q_LASTID)[0][0]
        return True

    """ Изменить запись """
    def _update(self,tn,struct,where):
        return self.run(self.tbs[tn].query_update(struct)+" where %s" % where)

    """ Удалить запись """
    def _delete(self,tn,where):
        return self.run(self.tbs[tn].query_delete(where))

    """ Пустая запись """
    def _empty(self,tn):
        return self.tbs[tn].empty_all_values()

    """ Удалить запись """
    def _delete(self,tn,where):
        return self.run(self.tbs[tn].query_delete(where))

    """ ------------------------------------------ """
    
    def _user_gets(self,rule,_if):
        return self.get(self.tb_users._gets(_if+str(rule)))

    def _user_add(self,aval):
        self.run(self.tb_users._add(aval))

    def _user_upd(self,iduser,aval):
        self.run(self.tb_users._upd(iduser,aval))

    def _user_get(self,login="",id=0):
        user=self.get(self.tb_users._get(login=login,id=id))
        if len(user)==0:
            return False
        else:
            user=self.tb_users.result2values(user[0])
            self.user=user
            return True

    def _user_auth(self,login,password):
        user=self.get(self.tb_users._get(login=login))
        if len(user)==0:
            return False
        else:
            user=self.tb_users.result2values(user[0])
            self.user=user
            if md5(password).hexdigest()==user['password']:
                return True
            else:
                return False

    def _types_add(self,pref,id,name):
        self.run(self.tb_types._add([pref,id,name]))

    def _types_get(self,pref):
        return self.get(self.tb_types._get(pref))

    def _discount_get(self,code):
        r=self.get(self.tb_discount._get(code))
        if len(r)==0:
            self.discount=None
            return False
        else:
            self.discount=self.tb_discount.result2values(r[0])
            return True

    def _read_sets(self,group=''):
        self.sets={}
        data = self.get(self.tb_sets._getall(group))
        for d in data:
            if d[3]==None:
                s='None'
            else:
                s=d[3]
            self.sets[d[2]]=s
        try:
            self.idplace=int(self.sets['idplace'])
            self.nkassa=int(self.sets['nkassa'])
        except:
            self.idpalce=1
            self.nkassa=1

    def _sets_get(self,group=''):
        sets={}
        data = self.get(self.tb_sets._getall(group))
        for d in data:
            if d[3]==None:
                s='None'
            else:
                s=d[3]
            sets[d[2]]=s
        return sets

    def _sets_add(self,g,n,v):
        self.run(self.tb_sets._add([g,n,v]))

    def _sets_upd(self,n,v):
        self.run(self.tb_sets._upd(n,v))
                
    
    def _search_shk(self,shk):
        self.price=self.get(self.tb_price._find_shk(shk))
        if len(self.price)==0:
            priceshk=self.get(self.tb_price_shk._find_shk(shk))
            if len(priceshk)==0:
                self.price=None
                self.price_shk=None
                return False
            priceshk=self.tb_price_shk.result2values(priceshk[0],False)
            if not self._price_get(priceshk['id']):
                self.price=None
                self.price_shk=None
                return False
            self.price['name']=priceshk['name']
            if priceshk['koef']!=0:
                self.price['cena']=priceshk['koef']*self.price['cena']
            else:
                self.price['cena']=priceshk['cena']
            return True
        else:
            self.price=self.tb_price.result2values(self.price[0],False)
        return True

    def _price_get(self,code=None):
        self.price=self.get(self.tb_price._get(code))
        if len(self.price)==0:
            self.price=None
            self.price_shk=None
            return False
        else:
            self.price=self.tb_price.result2values(self.price[0],False)
            self.price_shk=self.get(self.tb_price_shk._get(code,None))
            return True

    def _price_get_group(self,parent):
        if parent=="":
            parent="0"
        self.price=self.get(self.tb_price._get_group(parent))
        if len(self.price)==0:
            return False
        else:
            return True

    def _price_get_in_list(self,_list):
        price=self.get(self.tb_price._get_in_list(_list))
        if len(price)==0:
            return False
        else:
            self.price={}
            for p in price:
                self.price[p[0]]=self.tb_price.result2values(p,tostr=True)
            return True

    def _check_hd_get(self,iduser,id):
        self.ch_head=self.get(self.tb_check_head._get(iduser,id))
        if len(self.ch_head)==0:
            self.ch_head=None
            return False
        else:
            self.ch_head=self.tb_check_head.result2values(self.ch_head[0])
            self.ch_head['summa_wod']=self.ch_head['summa']-self.ch_head['discount_sum']
            self.ch_head['summa_pay']=self.ch_head['summa']-self.ch_head['discount_sum']-self.ch_head['bonus_discount']
            return True

    def _check_get(self,iduser,id):
        self.ch_head=self.get(self.tb_check_head._get(iduser,id))
        self.ch_cont=self.get(self.tb_check_cont._gets(iduser,id))
        if len(self.ch_head)==0:
            self.ch_head=None
            return False
        else:
            self.ch_head=self.tb_check_head.result2values(self.ch_head[0])
            self.ch_head['summa_wod']=self.ch_head['summa']-self.ch_head['discount_sum']
            self.ch_head['summa_pay']=self.ch_head['summa']-self.ch_head['discount_sum']-self.ch_head['bonus_discount']
            return True

    def _check_gets(self,iduser,_all):
        self.checks=self.get(self.tb_check_head._gets(iduser,_all))
        if len(self.checks)==0:
            return False
        else:
            #replace field puttime as str for json
            d=[]
            for p in range(len(self.checks)):
                pos=list(self.checks[p])
                pos[2]=str(pos[2])
                d.append(pos)
            self.checks=d
            return True

    def _check_json(self):
        if self.ch_head!=None:
            empty=False
        else:
            empty=True
            result={"empty":empty,"head":{},"cont":{}}
            return result
        head=self.ch_head
        head['puttime']=str(head['puttime'])
        result={"head":head,}
        cont={}
        for p in range(len(self.ch_cont)):
           pos = self.tb_check_cont.result2values(self.ch_cont[p],decode=True)
           del pos['date']
           del pos['time']
           cont[p] = pos
        head['itogo']=_round(head['summa']-head['bonus_discount']-head['discount_sum'],2)
        result={"empty":empty,"head":head,"cont":cont}
        return result


    def _check_update(self,iduser,id,struct):
        self.run(self.tb_check_head._upd(iduser,id,struct))
        
    def _check_load(self,iduser,id,curiduser):
        if not self._check_get(iduser,id):
            return False
        self.run(self.tb_check_head._clear(curiduser,0))
        self.run(self.tb_check_cont._clear(curiduser,0))
        self.run(self.tb_check_head._upd(iduser,id,{'id':0,'iduser':curiduser}))
        self.run(self.tb_check_cont._updid(iduser,id,0,iduser2=curiduser))
        return True

    def _check_delete(self,iduser,id):
        self.run(self.tb_check_head._del(iduser,id))
        self.run(self.tb_check_cont._del(iduser,id))

    def _check_save(self,iduser):
        if not self._check_get(iduser,0):
            return 0
        if len(self.ch_cont)==0:
            return 0
        self.run(self.tb_check_head._copyto(iduser,0))
        id=self.get(my.Q_LASTID)[0][0]
        self.run(self.tb_check_cont._updid(iduser,0,id))
        self.run(self.tb_check_head._clear(iduser,0))
        self.run(self.tb_check_cont._clear(iduser,0))
        return id

    def _check_create(self,iduser):
        self.run(self.tb_check_head._clear(iduser,0))
        self.run(self.tb_check_cont._clear(iduser,0))
        self.run(self.tb_check_head._new(iduser))
        id=self.get(my.Q_LASTID)
        self.run(self.tb_check_head._setcur(iduser,id[0][0]))

    def _check_pos_barcode(self,iduser,idcheck,barcode):
        r=self.get(self.tb_check_cont._find_barcode(iduser,idcheck,barcode))
        if len(r)==0:
            return False
        else:
            return True

    def _check_pos_get(self,iduser,idcheck,id):
        self.ch_cont_pos=self.get(self.tb_check_cont._get(iduser,idcheck,id))
        if len(self.ch_cont_pos)==0:
            self.ch_cont_pos=None
            return False
        else:
            self.ch_cont_pos=self.tb_check_cont.result2values(self.ch_cont_pos[0])
            return True

    def _check_pos_add(self,iduser,idcheck,a):
        self.run(self.tb_check_cont._add(iduser,idcheck,a))
        id=self.get(my.Q_LASTID)
        return id[0][0]

    def _check_pos_upd(self,iduser,idcheck,id,struct):
        self.run(self.tb_check_cont._upd(iduser,idcheck,id,struct))

    def _check_pos_upds(self,iduser,idcheck,struct):
        self.run(self.tb_check_cont._upds(iduser,idcheck,struct))

    def _check_pos_dels(self,iduser,idcheck,_list):
        self.run(self.tb_check_cont._dels(iduser,idcheck,_list))

    def _check_pos_info_set(self,iduser,idcheck,id,shcode=True,cena=None):
        if not self._check_pos_get(iduser,idcheck,id):
            return False
        code=self.ch_cont_pos["code"]
        if self.price!=None:
            if len(self.price_shk)>0:
                multiprice=1
            else:
                multiprice=0
            struct={}
            for f in self.tb_check_cont.fd_priceinfo:
                struct[f] = self.price[ f[2:] ]
            if cena!=None:
                struct["paramf1"]   = cena
            else:
                struct["paramf1"]   = self.price["cena"]
            struct["name"]          = self.price["name"]
            struct["multiprice"]    = multiprice
            if not shcode:
                del struct['p_shk']
            self.run(self.tb_check_cont._upd(iduser,idcheck,id,struct))
            return True
        else:
            return False


    def _trsc_to_check(self,iduser,id,ro=True,_reverse=False):
        self._check_create(iduser)
        if not self._trsc_get_check(id,tostr=False):
            return False
        fd_ident=['type','seller','errors','discount_card','discount_proc',\
        'bonus_card','bonus_proc','bonus_max','bonus_sum','bonus_type']
        fd_koef=['summa','discount_sum','bonus_discount','bonus']
        fd_koef_ct=['paramf2','paramf3','discount','dcount','bonus_discount','bonus']
        if _reverse:
            if  self.trsc_hd['type']==1:
                self.trsc_hd['type']=0
                _koef=-1
            else:
                self.trsc_hd['type']=1
                _koef=1
        else:
            if self.trsc_hd['type']==1:
                _koef=-1
            else:
                _koef=1
        struct={'ro':ro,'iduser':iduser}

        for n in fd_ident:
            struct[n] = self.trsc_hd[n]
        for n in fd_koef:
            struct[n] = _koef*self.trsc_hd[n]
        self._check_update(iduser,0,struct)

        for p in self.trsc_ct:
            struct={}
            for f in self.tb_check_cont.fieldsorder:
                if p.has_key(f):
                    if f in fd_koef_ct and p[f]!=None:
                        struct[f]=_koef*p[f]
                    else:
                        struct[f]=p[f]
            self._check_pos_add(iduser,0,struct)
        return True

    def _check_to_trsc(self,ncheck,nal,bnal,ispayed,isfiscal=0):
        fd_ident=['iduser','seller','type','errors','discount_card','discount_proc',\
        'bonus_card','bonus_proc','bonus_max','bonus_sum','bonus_type','egais_url','egais_sign']
        fd_koef=['summa','discount_sum','bonus_discount','bonus']
        fd_koef_ct=['paramf2','paramf3','discount','dcount','bonus_discount','bonus']

        if self.ch_head['type']==1:
            _koef=-1
        else:
            _koef=1
        struct={'ncheck':ncheck,'pay_nal':nal*_koef,'pay_bnal':bnal*_koef,'ispayed':ispayed,'isfiscal':isfiscal}

        dt = my.curdate2my()
        tm = my.curtime2my()
        struct['date']=dt
        struct['time']=tm

            
        struct['idplace']=self.idplace
        struct['nkassa']=self.nkassa
        
        for n in fd_ident:
            struct[n] = self.ch_head[n]
        for n in fd_koef:
            struct[n] = _koef*self.ch_head[n]

        self.run(self.tb_trsc_hd._add(struct))
        id=self.get(my.Q_LASTID)[0][0]
        if ncheck==0:
            self.run(self.tb_trsc_hd._upd(self.idplace,self.nkassa,id,{'ncheck':id}))

        for pos in self.ch_cont:
            p=self.tb_check_cont.result2values(pos)
            struct={}
            for f in self.tb_trsc_ct.record_add:
                if p.has_key(f):
                    if f in fd_koef_ct and p[f]!=None:
                        struct[f]=_koef*p[f]
                    else:
                        struct[f]=p[f]
            struct['idhd']=id
            self.run(self.tb_trsc_ct._add(struct))

        return True

    def _trsc_get_check(self,id,tostr=True):
        if id==None:
            trsc_hd=self.get("select * from tb_trsc_hd order by id limit 1")
            if len(trsc_hd)>0:
                id=trsc_hd[0][0]
        else:
            trsc_hd=self.get(self.tb_trsc_hd._get_check(self.idplace,self.nkassa,id))
        if len(trsc_hd)==0:
            return False
        self._trsc_hd = trsc_hd[0]
        self.trsc_hd = self.tb_trsc_hd.result2values(trsc_hd[0],tostr=tostr)
        trsc_ct=self.get(self.tb_trsc_ct._get_title(id))
        self.trsc_ct=[]
        for c in trsc_ct:
            d=self.tb_trsc_ct.result2values(c,tostr=tostr)
            d['name']=c[-1]
            self.trsc_ct.append(d)
        return True


    def _trsc_get(self,idzet=None,limit=1000):
        if not limit:
            limit=1000
        if idzet:
            self.Zet=self.get(self.tb_Zet._get(self.idplace,self.nkassa,idzet))
            if len(self.Zet)==0:
                return False
            (idbegin,idend)=self.Zet[0][8:10]
            chhd=self.get(self.tb_trsc_hd._get_Z(idbegin,idend))
            chct=self.get(self.tb_trsc_ct._get_Z(idbegin,idend))
        else:
            chhd=self.get(self.tb_trsc_hd._getup(limit))
            chct=self.get(self.tb_trsc_ct._getup(limit))
        data=[]
        curct=0
        for hd in chhd:
            idhd=hd[0]
            _hd=array4json(hd)
            _ct=[]
            while curct<len(chct) and idhd==chct[curct][1]:
                _c=array4json(chct[curct])
                _ct.append(_c)
                curct+=1
            data.append({'h':_hd,'b':_ct})
        return data
            
    def _trsc_updup(self,id1,id2,up):
        return self.run(self.tb_trsc_hd._updup(id1,id2,up))

    def _curZet_calc(self):
        if self._Zet_last():
            idbegin = self.ZetLast['end_ncheck']+1
        else:
            idbegin=None
        idend=None
        calcSum  = self.get(self.tb_trsc_hd._calc_sum    (self.idplace,self.nkassa,idbegin,idend))[0]
        calcCount = self.get(self.tb_trsc_hd._calc_count(self.idplace,self.nkassa,idbegin,None))[0]
        fd=['c_sale',
            'summa','summa_ret','summa_nal','summa_bnal',
            'discount','bonus','bonus_discount',
            'begin_ncheck','end_ncheck',
            'c_nofiscal','c_saled','nf_summa','nf_discount','nf_bonus_discount']
        self.curZet={}
        for i in range(len(fd)):
            self.curZet[fd[i]]=calcSum[i]
        fd=['c_return','c_cancel','c_error']
        for i in range(len(fd)):
            try:
                self.curZet[fd[i]]=int(calcCount[i])
            except:
                self.curZet[fd[i]]=0

    def _trsc_calc(self,idbegin=None,idend=None,full=True):
        self.run(self.tb_trsc_hd._recalc(idbegin,idend))
        calcSum     = self.get(self.tb_trsc_hd._calc_sum    (self.idplace,self.nkassa,idbegin,idend))[0]
        calcCount   = self.get(self.tb_trsc_hd._calc_count  (self.idplace,self.nkassa,idbegin,idend))[0]
        if idend==None:
            self._trsc_last()
        else:
            self.trsc=self._trsc_hd

        self._trsc_get_check(idbegin)
        if calcSum[0]==0:
            self.Zet={}
            self.Zet_ct=[]
            self.Zet['vir']=0
            self.Zet['c_sale']=0
            self.Zet['summa']=0
            self.Zet['summa_nal']=0
            self.Zet['summa_bnal']=0
            return False

        fd=['c_sale',
            'summa','summa_ret','summa_nal','summa_bnal',
            'discount','bonus','bonus_discount',
            'begin_ncheck','end_ncheck',
            'c_nofiscal','c_saled','nf_summa','nf_discount','nf_bonus_discount']

        self.Zet={  'begin_date':self.trsc_hd['date'],
                    'begin_time':self.trsc_hd['time'],
                    'end_date':self.trsc[3],
                    'end_time':self.trsc[4]}

        for i in range(len(fd)):
            self.Zet[fd[i]]=calcSum[i]

        fd=['c_return','c_cancel','c_error']
        for i in range(len(fd)):
            try:
                self.Zet[fd[i]]=int(calcCount[i])
            except:
                self.Zet[fd[i]]=0

        if self.Zet['summa']!=None:
            self.Zet['vir']=self.Zet['summa']-self.Zet['discount']-self.Zet['bonus_discount']
            self.Zet['summa_nal']=self.Zet['vir']-self.Zet['summa_bnal']
        else:
            self.Zet['vir']=0

        if self.Zet['nf_summa']!=None:
            self.Zet['nf_vir']=self.Zet['nf_summa']-self.Zet['nf_discount']-self.Zet['nf_bonus_discount']
        else:
            self.Zet['nf_vir']=0

        #Расчитываем дату Зет отчета
        t=self.sets['begin_time'].split(':')
        t=datetime.timedelta(0,int(t[0])*60*60+int(t[1])*60)
        if self.Zet['end_time']>t:
            self.Zet['date']=self.Zet['end_date']
        else:
            self.Zet['date']=self.Zet['end_date']-datetime.timedelta(1,0)

        for n in ('end_date','end_time','begin_date','begin_time','date'):
            self.Zet[n]=str(self.Zet[n])

        self.Zet_ct=[]
        if not full:
            return True

        calcCt=self.get(self.tb_trsc_hd._calc_ct(idbegin,idend))
        fd=['section','idgroup','code','alco','paramf1','paramf2','paramf3','discount','bonus','bonus_discount','isfiscal']
        for d in calcCt:
            ct={}
            for i in range(len(d)):
                ct[fd[i]]=d[i]
            self.Zet_ct.append(ct)
        return True

    def _trsc_last(self,_if=""):
        d=self.get(self.tb_trsc_hd._last(self.idplace,self.nkassa,_if))
        if len(d)==0:
            self.trsc=None
            return 0
        else:
            self.trsc=d[0]
            return d[0][0]

    def _trsc_filter(self,dt1,dt2,tm1,tm2,ncheck,tcheck,tpay,tclose,dcard,bcard,fiscal,error,discount,bonus,summa,alco,code,group):
        r=self.get(self.tb_trsc_hd._filter(self.idplace,self.nkassa,dt1,dt2,tm1,tm2,ncheck,tcheck,tpay,tclose,dcard,bcard,fiscal,error,discount,bonus,summa,alco,code,group))
        self.f_checks=[]
        for n in r:
            data=self.tb_trsc_hd.result2values(n,tostr=True)
            data['vir']=_round(float(data['summa'])-float(data['discount_sum'])-float(data['bonus_discount']),2)
            self.f_checks.append(data)

    def _Zet_last(self):
        d=self.get(self.tb_Zet._last(self.idplace,self.nkassa))
        if len(d)>0:
            self.ZetLast=self.tb_Zet.result2values(d[0])
            return True
        else:
            self.ZetLast=None
            return False

    def _Zet_update(self,id):
        r=self.run(self.tb_Zet._upd(id,self.Zet))
        if not r:
            print "not update"
            return False
        self.ZetID=id
        self.run(self.tb_Zet_cont._dels(id))
        for v in self.Zet_ct:
            v['idhd']=id
            self.run(self.tb_Zet_cont._add(v))
        return True

    def _Zet_add(self):
        r=self.run(self.tb_Zet._add(self.Zet))
        if not r:
            return False
        id=self.get(my.Q_LASTID)[0][0]
        self.ZetID=id
        for v in self.Zet_ct:
            v['idhd']=id
            self.run(self.tb_Zet_cont._add(v))
        return True

    def _Zet_gets(self,dt1,dt2,up=None):
        self.Zets=self.get(self.tb_Zet._gets(dt1,dt2,up))
        if len(self.Zets)==0:
            return False
        Zets=[]
        for v in self.Zets:
            struct=self.tb_Zet.result2values(v,tostr=True)
            Zets.append(struct)
        self.Zets=Zets
        return True

    def _Zet_upd(self,id,struct):
        return self.run(self.tb_Zet._upd(id,struct))

    def _Zet_get(self,id):
        self.Zet=self.get(self.tb_Zet._get(self.idplace,self.nkassa,id))
        if len(self.Zet)==0:
            return False
        else:
            self.Zet=self.tb_Zet.result2values(self.Zet[0],tostr=True)
        Zet_ct=self.get(self.tb_Zet_cont._get(id))
        self.Zet_ct=[]
        for n in Zet_ct:
            self.Zet_ct.append(self.tb_Zet_cont.result2values(n,tostr=True))
        return True

    def _Zet_get_html(self,id):
        self.Zet=self.get(self.tb_Zet._get(self.idplace,self.nkassa,id))
        if len(self.Zet)==0:
            return False
        else:
            self.Zet=self.tb_Zet.result2values(self.Zet[0])
        self.Zet_ct=self.get(self.tb_Zet_cont._gethtml(id))
        return True

    def egais_ostat_clear(self):
        self.run(self.tb_egais_ostat.query_truncate())

    def egais_ostat_add(self,struct):
        self.run(self.tb_egais_ostat._add(struct))

    def egais_places_clear(self):
        self.run(self.tb_egais_places.query_truncate())

    def egais_places_add(self,struct):
        self.run(self.tb_egais_places._add(struct))

    def egais_docs_hd_del(self,id):
        if self.run(self.tb_egais_docs_hd._del(id)):
            return self.run(self.tb_egais_docs_ct._del(id))
        return False

    def egais_docs_hd_add(self,struct):
        if self.run(self.tb_egais_docs_hd._add(struct)):
            return self.get(my.Q_LASTID)[0][0]
        else:
            return 0

    def egais_docs_ct_add(self,struct):
        if self.run(self.tb_egais_docs_ct._add(struct)):
            return self.get(my.Q_LASTID)[0][0]
        else:
            return 0

    def egais_docs_hd_upd(self,id,struct):
        return self.run(self.tb_egais_docs_hd._upd(id,struct))

    def egais_docs_del(self,id):
        r=self.run(self.tb_egais_docs_hd._del(id))
        self.run(self.tb_egais_docs_ct._del(id))
        return r

    def egais_docs_ct_getpos(self,idd,id):
        r=self.get(self.tb_egais_docs_ct._getpos(idd,id))
        if len(r)==0:
            return False
        self.egais_doc_ct=self.tb_egais_docs_ct.result2values(r[0],tostr=True)
        return True

    def egais_docs_ct_upd(self,idd,id,struct):
        return self.run(self.tb_egais_docs_ct._upd(idd,id,struct))

    def egais_docs_ct_updId(self,idd,id,struct):
        return self.run(self.tb_egais_docs_ct._updId(idd,id,struct))
            
    def egais_docs_find(self,_type,recv_RegId,send_RegId,wb_NUMBER):
        self.egais_doc=self.get(self.tb_egais_docs_hd._find(_type,recv_RegId,send_RegId,wb_NUMBER))
        if len(self.egais_doc)>0:
            self.egais_doc=self.egais_doc[0]
            return True
        else:
            return False

    def egais_find_replyId(self,reply_id):
        self.egais_doc=self.get(self.tb_egais_docs_hd._find_replyId(reply_id))
        if len(self.egais_doc)>0:
            self.egais_doc=self.egais_doc[0]
            return True
        else:
            return False

    def egais_find_ttn(self,ttn):
        self.egais_doc=self.get(self.tb_egais_docs_hd._find_ttn(ttn))
        if len(self.egais_doc)>0:
            self.egais_doc=self.egais_doc[0]
            return True
        else:
            return False

    def egais_get_postav(self):
        postav=self.get(self.tb_egais_docs_hd._get_postav())
        return postav
    
    def egais_get_ostat(self):
        ostat=self.get(self.tb_egais_ostat._gets())
        return ostat

    def egais_get_mydocs(self,_type,status,postav,dt1,dt2):
        postav=self.get(self.tb_egais_docs_hd._get_docs(_type,status,postav,dt1,dt2))
        d=[]
        if len(postav)>0:
            for p in postav:
                d.append(self.tb_egais_docs_hd.result2values(p,tostr=True))
        return d

    def egais_get_mydoc(self,idd):
        hd=self.get(self.tb_egais_docs_hd._get(idd))
        self.egais_doc_hd=[]
        self.egais_doc_ct=[]
        if len(hd)==0:
            return False
        self.egais_doc_hd=self.tb_egais_docs_hd.result2values(hd[0],tostr=True)
        ct=self.get(self.tb_egais_docs_ct._get(idd))
        for p in ct:
            self.egais_doc_ct.append(self.tb_egais_docs_ct.result2values(p,tostr=True))
        return True

    def _actions_gets(self):
        return self.get(self.tb_actions_hd._gets())

    def _tlist_gets(self):
        return self.get(self.tb_tlist._gets())

    def boxes_get_sublink(self,id):
        return self._select(TB_BOXES_HD," idhd=%s" % id,dttm2str=True)

    def _zakaz_copy(self,iduser,id):
        hd=self._getid(TB_BOXES_HD,id)
        if hd==None:
            return False
        if hd['status']!=3:
            return False
        sub=self.boxes_get_sublink(id)
        a=[str(hd['id'])]
        for s in sub:
            a.append(str(s['id']))
        l=",".join(a)
        d=self._select(TB_BOXES_CT," idhd in (%s) and storno=0" % l,dttm2str=True,fields=['idhd','code','count'])
        for r in d:
            idpos=self._check_pos_add(iduser,0,{'nbox':id,'code':str(r['code']),'paramf2':r['count']})
            self._price_get(r['code'])
            self._check_pos_info_set(iduser,0,idpos)
        return True

    def _zakaz_delete(self,iduser,id):
        self._delete(TB_CHECK_CONT,"iduser=%s and idcheck=0 and nbox=%s" % (iduser,id))
        return True

    def _create(self):
        if self.open():
            self.run("drop user '%s'@'localhost'" % MYSQL_USER)
            self.run("drop database %s" % DATABASE)
            self.run("create database %s" % DATABASE)
            self.run("create user '%s'@'localhost' IDENTIFIED BY '%s'" % (MYSQL_USER,MYSQL_PASSWORD))
            self.run("grant all on "+DATABASE+".* to '%s'@'localhost'" % MYSQL_USER)
            self.run("flush privileges")
            self.run("use %s" % DATABASE)

            self.run(self.tb_sets._create())
            self._sets_add('server','version','2.0')
            self._sets_add('server','server_port','10110')
            self._sets_add('server','dtprint_ip','localhost')
            self._sets_add('server','dtprint_port','10111')
            self._sets_add('server','backoffice_ip','IceServ')
            self._sets_add('server','backservice_port','10100')
            self._sets_add('server','bonus_port','7172')
            self._sets_add('server','dtprint_passwd','dtpadm')
            self._sets_add('server','regid','beerkem')
            self._sets_add('server','egais_ip','localhost')
            self._sets_add('server','regpassword','766766')
            self._sets_add('server','temperature','0')
            self._sets_add('server','upgrade','0')
            self._sets_add('server','prize_port','7174')

            self._sets_add('client','timeout_ping','15')
            self._sets_add('client','timeout_query','60')
            self._sets_add('client','css','default')
            self._sets_add('client','scale_prefix','21')
            self._sets_add('client','user_prefix','111')
            self._sets_add('client','discount_prefix','222')
            self._sets_add('client','bonus_prefix','777')
            self._sets_add('client','site','site')

            self._sets_add('magazine','texthead','')
            self._sets_add('magazine','textfoot','')
            self._sets_add('magazine','orgname','')
            self._sets_add('magazine','placename','')
            self._sets_add('magazine','inn','4205183793')
            self._sets_add('magazine','kpp','420501001')
            self._sets_add('magazine','logo','')
            self._sets_add('magazine','idplace','1')
            self._sets_add('magazine','nkassa','1')
            self._sets_add('magazine','calcost','0')
            self._sets_add('magazine','pricenum','0')
            self._sets_add('magazine','messagetype','default')
            self._sets_add('magazine','begin_time','06:00:00')
            self._sets_add('magazine','action','0')
            self._sets_add('magazine','sets','0')
            self._sets_add('magazine','nofiscal_proc','0')
            
            self._sets_add('device','dev_scanner','')
            self._sets_add('device','d_name','None')
            self._sets_add('device','d_speed','8')
            self._sets_add('device','d_devtype','KKM_FPRINT')
            self._sets_add('device','d_printsh','1')
            self._sets_add('device','d_autonull','1')
            self._sets_add('device','d_autobox','1')
            self._sets_add('device','d_summertm','1')
            self._sets_add('device','d_autocut','1')
            self._sets_add('device','d_ignore','0')
            self._sets_add('device','d_ncheck','1')

            self.run(self.tb_trsc_hd._create())
            self.run(self.tb_trsc_ct._create())
            self.run(self.tb_price._create())
            self.run(self.tb_price_shk._create())
            self.run(self.tb_discount._create())
            self.run(self.tb_check_head._create())
            self.run(self.tb_check_cont._create())
            self.run(self.tb_users._create())
            self.run(self.tb_types._create())
            self.run(self.tb_Zet._create())
            self.run(self.tb_Zet_cont._create())
            self.run(self.tb_egais_places._create())
            self.run(self.tb_egais_ostat._create())
            self.run(self.tb_egais_docs_hd._create())
            self.run(self.tb_egais_docs_ct._create())
            self.run(self.tb_egais_docs_need._create())
            self.run(self.tb_actions_hd._create())
            self.run(self.tb_tlist._create())

            self._types_add('us',10,u'Продавец')
            self._types_add('us',50,u'Кассир')
            self._types_add('us',100,u'Админ')

            self._user_add(['admin' ,md5("678543").hexdigest(),TYPE_USER['ADMIN']])
            self._user_add(['kassir',md5("766766").hexdigest(),TYPE_USER['KASSIR']])
            self._user_add(['seller',md5("111").hexdigest()   ,TYPE_USER['SELLER']])
            print "created database"
        else:
            print "error.not_open"

    def price_add(self,values):
        self.run(self.tb_price._add(values))

    def price_upd(self,values,_type):
        code=values[0]
        r=self.get(self.tb_price._get(code))
        if len(r)>0:
            struct=self.tb_price.result2values(values,decode=False)
            if _type=='clear':
                pass
            elif _type=='keep' or _type=='add':
                ost=struct['ostatok']
                del struct['ostatok']
            self.run(self.tb_price._upd(code,struct))
            if _type=='add':
                self.run(self.tb_price._upd_grow(code,ost))
        else:
            self.price_add(values)

    def price_add_shk(self,values):
        if not self.run(self.tb_price_shk._add(values)):
            print values[0:2]

    def price_upd_shk(self,code,shk,values):
        r=self.get(self.tb_price_shk._get(code,shk))
        if len(r)>0:
            self.run(self.tb_price_shk._upd(code,shk,values))
        else:
            self.price_add_shk([code,shk]+values)
            

    def price_clear(self):
        self.run('truncate tb_price_shk')
        return self.run('truncate tb_price')

    def price_load(self,fname):
        """ IceCash format like Shtrihm
            1   : Код товара
            2   : Штрихкод
            3   : Наименование
            4   : Литраж
            5   : Цена
            6   : Остаток
            7   : *Схема скидок
            8   : Признак весового товара
            9   : Номер секции
            10  : *Максимальная скидка
            11  : *Тип номенклатуры
            12  : Признак алкоголя по ЕГАИС
            13  : *Минимальная цена
            14  : *Максимальная цена
            15  : reserved2
            16  : Идентификатор группы этого товара
            17  : Признак товара (не группы)
        """
        try:
            f = open(fname,'r')
        except:
            return False
        line = f.readline()
        line=line.rstrip("\n\r")

        Shash = Str2Shash(line,";","=")
        if not Shash.has_key("#IceCash"):
            print "price_load: error: not #IceCash file"
            f.close()
            return False
        if not Shash.has_key("type"):
            print "price_load: error: no type param "
            f.close()
            return False
        if Shash["type"]!="price":
            print "price_load: error: type<>IceCash.price"
            f.close()
            return False
        if not Shash.has_key("sheme_record"):
            Shash["sheme_record"]="clear"
        if not Shash.has_key("sheme_count"):
            Shash["sheme_count"]="clear"

        if Shash["sheme_record"]=="clear":
            print "price_load: clear"
            insert=True
            self.price_clear()
        else:
            insert=False

        for line in f.readlines():
            if line=='':
                continue
            line=line.decode('cp1251').encode('utf8')
            arr=line.split(';')
            try:
                arr[3]=float(arr[3])
            except:
                arr[3]=0
            code=arr[0]
            pref = code[0]
            if re.match(r'^#(\d)*$',code):
                if len(arr)<6:
                    continue
                (code,shk,n1,n2,cena,koef)=arr[0:6]
                code=code.lstrip('#')
                if koef=="" or koef=="0":
                    koef=1
                if not insert:
                    self.price_upd_shk(code,shk,[n1,cena,koef])
                else:
                    self.price_add_shk([code,shk,n1,cena,koef])
            elif re.match(r'^(\d)*$',code):
                if len(arr)<17:
                    continue
                if not insert:
                    self.price_upd(arr,Shash['sheme_count'])
                else:
                    self.price_add(arr)
        return True
"""
db = dbIceCash(DATABASE, "localhost", MYSQL_USER, MYSQL_PASSWORD)
if db.open():
#    db.price_load("site/download/price/pos1.spr")
    db._check_create(112)
    db.close()
"""
