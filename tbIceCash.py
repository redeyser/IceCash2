#!/usr/bin/python
# -*- coding: utf-8
# version 2.000
"""
    Tables of IceCash
"""
import my
from md5 import md5


class tb_sets(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('group','s')
        self.addfield('name','s')
        self.addfield('value','s')

    def _create(self):
        q="""create table `%s` (
        `id`    int(4) unsigned NOT NULL AUTO_INCREMENT,
        `group` char(64) default 'simple',
        `name`  char(64) default 'simple',
        `value` char(255) default '',
        primary key (`id`),
        unique  key `name` (`name`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _get(self,name):
        return self.query_select(['value']," where name='%s'" % name)

    def _getall(self,group=''):
        if group!='':
            _if=" where `group`='%s'" % group
        else:
            _if=""
        return self.query_all_select()+_if

    def _add(self,arrvalues):
        struct = self.set_values(['group','name','value'],arrvalues)
        return self.query_insert(struct)

    def _upd(self,name,value):
        struct = self.set_values(['value'],[value])
        return self.query_update(struct)+" where name='%s'" % name

    def _upd_post(self,post,group=''):
        struct={}
        for k in post.keys():
            struct[k]=post[k].value
        if group!='':
            _if=" and `group`='%s'" % group
        else:
            _if=""
        queries=[]
        for k,v in struct.items():
            queries.append(self.query_update({'value':v})+" where name='%s' %s" % (k,_if))
        return queries

class tb_users(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('login','s')
        self.addfield('password','s')
        self.addfield('type','d')
        self.addfield('code','s')
        self.addfield('idtab','d')
        self.addfield('css','s')
        self.addfield('cur_price','s')
        self.addfield('printer','s')
        self.record_add = self.fieldsorder[1:4] 

    def _create(self):
        q="""create table `%s` (
        `id`         int(4) unsigned NOT NULL AUTO_INCREMENT,
        `login`      char(32) default '',
        `password`   char(32) default '',
        `type`       tinyint(1),
        `code`       char(24) default '',
        `idtab`      int(4) default 0,
        `css`        char(100) default '',
        `cur_price`  char(24) default '',
        `printer`    char(24) default '',
        primary key (`id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _clear(self):
        return self.empty_all_values()

    def _add(self,arrvalues):
        struct = self.set_values(self.record_add,arrvalues)
        return self.query_insert(struct)

    def _get(self,login="",id=0):
        if login=="":
            _if="id=%d" % id
        else:
            _if="login='%s'" % login
        return self.query_all_select()+" where %s" % _if

    def _del(self,id):
        return self.query_delete("id=%d" % id)

    def _gets(self,ifrule):
        return "select *,(select name from tb_types where pref='us' and id=`type`) as typename\
        from %s where `type`%s" % (self.tablename,ifrule)

    def _pre_post(self,struct):
        if struct.has_key("password"):
            password=md5(struct["password"]).hexdigest()
        else:
            password=""
        my.del_empty_hash(struct,"type")
        my.del_empty_hash(struct,"password")
        my.ch_hash(struct,"password",password)
        return struct

    def _upd(self,id,struct):
        return self.query_update(struct)+" where id=%d" % id

    def _upd_post(self,id,post):
        struct = self.post2struct(post,['login','password','type','code','idtab','css','printer'])
        struct = self._pre_post(struct)
        return self.query_update(struct)+" where id=%d" % id

    def _add_post(self,post):
        struct = self.post2struct(post,self.record_add)
        struct = self._pre_post(struct)
        return self.query_insert(struct)

class tb_trsc_hd(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('idplace','d')
        self.addfield('nkassa','d')

        self.addfield('date','D')
        self.addfield('time','t')

        self.addfield('type','d')
        self.addfield('iduser','d')
        self.addfield('seller','d')

        self.addfield('ncheck','d')
        self.addfield('ispayed','d')
        self.addfield('pay_nal','f')
        self.addfield('pay_bnal','f')

        self.addfield('summa','f')
        self.addfield('discount_card','s')
        self.addfield('bonus_card','s')
        self.addfield('discount_proc','f')
        self.addfield('bonus_proc','f')
        self.addfield('bonus_max','f')
        self.addfield('bonus_sum','f')

        self.addfield('bonus','f')
        self.addfield('discount_sum','f')
        self.addfield('bonus_discount','f')
        self.addfield('bonus_type','d')
        self.addfield('errors','s')
        self.addfield('up','d')
        self.addfield('isfiscal','d')
        self.addfield('egais_url','s')
        self.addfield('egais_sign','s')
        self.record_add = self.fieldsorder[1:] 

    def _add(self,struct):
        return self.query_insert(struct)

    def _upd(self,idplace,nkassa,id,struct):
        return self.query_update(struct)+" where idplace=%d and nkassa=%d and id=%d" % (idplace,nkassa,id)

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id`       int(10) unsigned NOT NULL AUTO_INCREMENT,
          `idplace`  int(4),
          `nkassa`   tinyint(2) unsigned NOT NULL,

          `date`     date NOT NULL,
          `time`     time NOT NULL,

          `type`     tinyint(1) NOT NULL,
          `iduser`   int(4),
          `seller`   smallint(4) unsigned NOT NULL,

          `ncheck`   int(5) unsigned DEFAULT '0',
          `ispayed`  tinyint(1) unsigned default 0,
          `pay_nal`  double(8,2) default 0,
          `pay_bnal` double(8,2) default 0,

          `summa`     double(8,2) default 0,
          `discount_card`  varchar(24) default '',
          `bonus_card` varchar(24) default '',
          `discount_proc` double(8,4) default 0,
          `bonus_proc` double(8,4) default 0,
          `bonus_max` double(8,4) default 0,
          `bonus_sum`  double(8,2) default 0,

          `bonus`     double(8,2) default 0,
          `discount_sum`  double(8,2) default 0,
          `bonus_discount`  double(8,2) default 0,
          `bonus_type`  tinyint(1) unsigned default 0,
          `errors`    varchar(4)  default '',
          `up`      tinyint(1) default 0,
          `isfiscal`      tinyint(1) default 0,
          `egais_url`     varchar(255) default '',
          `egais_sign`    varchar(255) default '',

          PRIMARY KEY (`id`),
          KEY `pl` (`idplace`,`nkassa`,`id`),
          KEY `tm` (`idplace`,`nkassa`,`date`,`time`),
          KEY `up` (`idplace`,`nkassa`,`up`,`date`,`time`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _getup(self,limit):
        return self.query_all_select()+" where up=0 order by idplace,nkassa,id limit %d" % limit

    def _updup(self,id1,id2,up):
        return self.query_update({'up':up})+" where id>=%d and id<=%d" % (id1,id2)

    def _get_Z(self,idbegin=None,idend=None):
        s1=''
        s2=''
        if (idbegin!=None):
            s1+=" and `id`>='%d'" % idbegin
        if (idend!=None):
            s2+=" and `id`<='%d'" % idend
        s=s1+s2
        if s!='':
            s=' where id>0 '+s
        return self.query_all_select()+" %s" % (s)

    def _recalc(self,idbegin=None,idend=None):
        s1=''
        s2=''
        v1=''
        v2=''
        if (idbegin!=None):
            s1+=" and hd.id>=%d" % idbegin
            v1+=" and idhd>=%d" % idbegin
        if (idend!=None):
            s2+=" and hd.id<=%d" % idend
            v2+=" and idhd<=%d" % idend
        s=s1+s2
        v=v1+v2
        q= "update tb_trsc_hd as hd, (select idhd,sum(discount) as dis,sum(bonus_discount) as bdis,sum(ParamF3) as p3,sum(bonus) as bs \
        from tb_trsc_ct where storno=0 %s group by idhd) as ct\
        set hd.summa=ct.p3,hd.discount_sum=ct.dis,hd.bonus=ct.bs,hd.bonus_discount=ct.bdis\
        where hd.id=ct.idhd %s" % (v,s)
        #print q
        return q

    def _calc_sum(self,idbegin=None,idend=None):
        s1=''
        s2=''
        if (idbegin!=None):
            s1+=" and `id`>='%d'" % idbegin
        if (idend!=None):
            s2+=" and `id`<='%d'" % idend
        s=s1+s2
        return "select \
        count(*),\
        sum(summa),\
        sum(if(`type`=1,summa,0)),\
        sum(pay_nal),\
        sum(pay_bnal),\
        sum(discount_sum),\
        sum(bonus),\
        sum(bonus_discount),\
        min(id),max(id)\
        from %s where ispayed=1 %s" % (self.tablename,s)

    def _calc_count(self,idbegin=None,idend=None):
        s1=''
        s2=''
        if (idbegin!=None):
            s1+=" and `id`>='%d'" % idbegin
        if (idend!=None):
            s2+=" and `id`<='%d'" % idend
        s=s1+s2
        if s!='':
            s=' where id>=0 '+s
        return "select \
        sum(if(type=1,if(ispayed=1,1,0),0)),\
        sum(if(ispayed=0,1,0)),\
        sum(if(errors<>'',1,0))\
        from %s %s" % (self.tablename,s)

    def _calc_ct(self,idbegin=None,idend=None):
        s1=''
        s2=''
        if (idbegin!=None):
            s1+=" and `idhd`>='%d'" % idbegin
        if (idend!=None):
            s2+=" and `idhd`<='%d'" % idend
        s=s1+s2
        return "select ct.p_section,ct.p_idgroup,ct.code,ct.p_alco,ct.paramf1,sum(ct.paramf2),sum(ct.paramf3),\
        sum(ct.discount),sum(ct.bonus),sum(ct.bonus_discount)\
        from tb_trsc_hd as hd,tb_trsc_ct as ct where hd.id=ct.idhd and hd.ispayed=1 and ct.storno=0 %s group by code" % (s)

    def _last(self,idplace,nkassa,_if=""):
        if _if!="":
            _if=" and "+_if
        return self.query_all_select()+"where idplace=%d and nkassa=%d %s order by id desc limit 1" % (idplace,nkassa,_if)

    def _filter(self,idplace,nkassa,dt1,dt2,tm1,tm2,ncheck,tcheck,tpay,tclose,dcard,bcard,fiscal,error,discount,bonus,summa,alco,code,group):
        e='and'
        _dt1=""
        _dt2=""
        _tm1=""
        _tm2=""
        _ncheck=""
        _tcheck=""
        _tpay=""
        _tclose=""
        _dcard=""
        _bcard=""
        _fiscal=""
        _error=""
        _discount=""
        _bonus=""
        _code=""
        _alco=""
        _group=""
        _summa=""
        if dt1:
            _dt1=e+" hd.date>='%s'" % dt1
        if dt2:
            _dt2=e+" hd.date<='%s'" % dt2
        if tm1:
            _tm1=e+" hd.time>='%s'" % tm1
        if tm2:
            _tm2=e+" hd.time<='%s'" % tm2
        if ncheck != None:
            _ncheck=e+" hd.ncheck='%s'" % ncheck
        if tcheck != None:
            _tcheck=e+" hd.type='%s'" % tcheck
        if tpay != None:
            if tpay=='0':
                _tpay=e+" pay_nal<>0 and pay_bnal=0"
            else:
                _tpay=e+" pay_nal=0 and pay_bnal<>0"
        if tclose != None:
            _tclose=e+" hd.ispayed=%s" % tclose
        if dcard != None:
            _dcard=e+" hd.discount_card<>''"
        if bcard != None:
            _bcard=e+" hd.bonus_card<>''"
        if fiscal != None:
            _fiscal=e+" hd.isfiscal=0"
        if error != None:
            _error=e+" hd.errors<>''"
        if  alco!= None:
            _alco=e+" hd.egais_sign<>''"
        if discount != None:
            _discount=e+" (hd.discount_sum+hd.bonus_discount)>%s" % discount
        if bonus != None:
            _bonus=e+" hd.bonus>%s" % bonus
        if code != None:
            _code=e+" ct.code=%s" % code
        if group != None:
            _group=e+" ct.p_idgroup=%s" % group
        if summa != None:
            _summa=e+" (hd.summa-hd.discount_sum-hd.bonus_discount)>=%s" % summa

        self.query_all_select()
        #q= "select hd.* from tb_trsc_hd as hd,tb_trsc_ct as ct where hd.id=ct.idhd and idplace=%d and nkassa=%d %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s order by id"\
        q= "select distinct hd.* from tb_trsc_hd as hd,tb_trsc_ct as ct where hd.id=ct.idhd and idplace=%d and nkassa=%d %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s %s order by id"\
        % (idplace,nkassa,_dt1,_dt2,_tm1,_tm2,_ncheck,_tcheck,_tpay,_tclose,_dcard,_bcard,_fiscal,_error,_discount,_bonus,_summa,_alco,_code,_group)
        #print q
        return q

    def _get_check(self,idplace,nkassa,id):
        q=self.query_all_select()+" where id=%d and idplace=%d and nkassa=%d" % (id,idplace,nkassa)
        return q

class tb_trsc_ct(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('idhd','d')

        self.addfield('date','D')
        self.addfield('time','t')

        self.addfield('code','d')
        self.addfield('storno','d')

        self.addfield('p_idgroup','d')
        self.addfield('p_section','d')
        self.addfield('p_cena','f')
        self.addfield('p_sheme','d')
        self.addfield('p_max_skid','f')
        self.addfield('p_real','d')
        self.addfield('p_type','d')
        self.addfield('p_alco','d')
        self.addfield('p_minprice','f')
        self.addfield('p_maxprice','f')

        self.addfield('multiprice','d')

        self.addfield('paramf1','f')
        self.addfield('paramf2','f')
        self.addfield('paramf3','f')

        self.addfield('mark','s')
        self.addfield('dcount','f')
        self.addfield('discount','f')
        self.addfield('bonus','f')
        self.addfield('bonus_discount','f')
        self.addfield('p_litrag','f')
        self.addfield('p_shk','s')
        self.addfield('barcode','s')
        self.record_add = self.fieldsorder[1:] 

    def _add(self,struct):
        return self.query_insert(struct)

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id`          int(4) unsigned NOT NULL AUTO_INCREMENT,
          `idhd`        int(4),
          `date`        date NOT NULL,
          `time`        time NOT NULL,
          `code`        varchar(24) default '',
          `storno`      tinyint(1) default 0,

          `p_idgroup`  varchar(24) DEFAULT '0',
          `p_section`  tinyint(1)  DEFAULT 1,
          `p_cena`     double(8,2) default 0,
          `p_sheme`    tinyint(1)  default 0,
          `p_max_skid` double(8,2) default 0,
          `p_real`     tinyint(1)  default 0,
          `p_type`     tinyint(1)  default 0,
          `p_alco`     tinyint(1)  default 0,
          `p_minprice` double(8,2) default 0,
          `p_maxprice` double(8,2) default 0,

          `multiprice` tinyint(3) unsigned default 0,

          `paramf1`  double(8,2) DEFAULT 0,
          `paramf2`  double(7,3) DEFAULT 1,
          `paramf3`  double(8,2) DEFAULT 0,
          `mark`     char(6) default '',
          `dcount`   double(7,3),

          `discount`  double(8,2) DEFAULT 0,
          `bonus`     double(8,2) DEFAULT 0,
          `bonus_discount`  double(8,2) default 0,
          `p_litrag`  double(8,4) DEFAULT 0,
          `p_shk`     varchar(24) DEFAULT '0',
          `barcode`   varchar(68) default '',
          PRIMARY KEY (`idhd`,`id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _getup(self,limit):
        return "select ct.* from tb_trsc_ct as ct,\
        (select id from tb_trsc_hd where up=0 order by idplace,nkassa,id limit %d) as hd\
        where hd.id=ct.idhd" % (limit)

    def _get_title(self,id):
        self.query_all_select()
        return "select *,(select name from tb_price where tb_price.id=ct.code) as price from %s as ct where `idhd`=%d" % (self.tablename,id)

    def _get(self,id):
        return self.query_all_select()+" where `idhd`=%d" % (id)

    def _get_Z(self,idbegin=None,idend=None):
        s1=''
        s2=''
        if (idbegin!=None):
            s1+=" and `idhd`>='%d'" % idbegin
        if (idend!=None):
            s2+=" and `idhd`<='%d'" % idend
        s=s1+s2
        if s!='':
            s=' where id>0 '+s
        return self.query_all_select()+" %s" % (s)

class tb_check_head(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('iduser','d')
        self.addfield('id','d')
        self.addfield('puttime','D')
        self.addfield('type','d')
        self.addfield('cursor','d')
        self.addfield('seller','d')
        self.addfield('comment','s')
        self.addfield('summa','f')
        self.addfield('discount_proc','f')
        self.addfield('discount_sum','f')
        self.addfield('discount_card','s')
        self.addfield('bonus_card','s')
        self.addfield('bonus','f')
        self.addfield('bonus_proc','f')
        self.addfield('bonus_max','f')
        self.addfield('bonus_sum','f')
        self.addfield('bonus_type','d')
        self.addfield('bonus_discount','f')
        self.addfield('errors','s')
        self.addfield('ro','d')
        self.addfield('bonus_payed','d')
        self.addfield('egais_xml','s')
        self.addfield('egais_url','s')
        self.addfield('egais_sign','s')
        self.addfield('idsystem','d')
        self.addfield('idprize','d')
        self.addfield('fio','s')

        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `iduser`   int(10),
          `id`       int(10) unsigned NOT NULL AUTO_INCREMENT,
          `puttime`  timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
          `type`     tinyint(3) unsigned  default 0,
          `cursor`   tinyint(3) unsigned  default 0,
          `seller`   smallint(4) unsigned default 0,
          `comment`  char(255) default '',
          `summa`     double(8,2) default 0,
          `discount_proc` double(8,4) default 0,
          `discount_sum`  double(8,2) default 0,
          `discount_card`  char(24) default '',
          `bonus_card`  char(24) default '',
          `bonus`  double(8,2) default 0,
          `bonus_proc` double(8,4) default 0,
          `bonus_max` double(8,4) default 0,
          `bonus_sum`  double(8,2) default 0,
          `bonus_type`   tinyint(3) unsigned  default 0,
          `bonus_discount`  double(8,2) default 0,
          `errors`   char(4) default '',
          `ro`   tinyint(1) default 0,
          `bonus_payed`   tinyint(1) default 0,
          `egais_xml` mediumtext,
          `egais_url` char(255) default '',
          `egais_sign` char(255) default '',
          `idsystem` tinyint(1) default 0,
          `idprize` int(4) default 0,
          `fio` char(100) default '',
          PRIMARY KEY (`iduser`,`id`),
          KEY `sel` (`puttime`,`seller`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _where(self,iduser,id):
        return "iduser=%d and id=%d" % (iduser,id)

    def _new(self,iduser):
        return self.query_insert({"iduser":str(iduser),"summa":"0"})
    
    def _setcur(self,iduser,id):
        return self.query_update({"id":"0"})+" where "+self._where(iduser,id)

    def _copyto(self,iduser,id):
        return "insert into %s select * from %s where %s" % (self.tablename,self.tablename,self._where(iduser,id))

    def _clear(self,iduser,id):
        return self.query_delete(self._where(iduser,id))

    def _get(self,iduser,id):
        return self.query_all_select()+" where "+self._where(iduser,id)

    def _gets(self,iduser,_all):
        if not _all:
            where = " where id>0 and iduser=%d" % iduser
        else:
            where=" where id>0"
        return "select *,(select login from tb_users where iduser=tb_users.id) as user from "+self.tablename+" "+where+" order by puttime desc"

    def _upd(self,iduser,id,struct):
        return self.query_update(struct)+" where "+self._where(iduser,id)

    def _del(self,iduser,id):
        return self.query_delete("iduser=%d and id=%d" % (iduser,id))

class tb_check_cont(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('idcheck','d')
        self.addfield('iduser','d')
        self.addfield('id','d')
        self.addfield('date','D')
        self.addfield('time','t')
        self.addfield('code','s')
        self.addfield('name','s')
        self.addfield('storno','d')

        self.addfield('p_idgroup','s')
        self.addfield('p_section','d')
        self.addfield('p_cena','f')
        self.addfield('p_sheme','d')
        self.addfield('p_max_skid','f')
        self.addfield('p_real','d')
        self.addfield('p_type','d')
        self.addfield('p_alco','d')
        self.addfield('p_minprice','f')
        self.addfield('p_maxprice','f')

        self.addfield('multiprice','d')
        self.addfield('paramf1','f')
        self.addfield('paramf1','f')
        self.addfield('paramf2','f')
        self.addfield('paramf3','f')
        self.addfield('mark','s')
        self.addfield('dcount','f')

        self.addfield('discount','f')
        self.addfield('bonus','f')
        self.addfield('bonus_discount','f')
        self.addfield('p_litrag','d')

        self.addfield('ean','s')
        self.addfield('barcode','s')
        self.addfield('p_shk','s')
        self.addfield('discount_pos','f')
        self.addfield('bonus_pos','f')
        self.addfield('nbox','d')
            
        self.fd_priceinfo=[]
        for i in self.fieldsorder:
            if i[:2]=="p_":
                self.fd_priceinfo.append(i)


    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `iduser`      int(4),
          `idcheck`     int(4),
          `id`          int(4) unsigned NOT NULL AUTO_INCREMENT,
          `date`     date NOT NULL,
          `time`     time NOT NULL,
          `code`     char(24) default '0',
          `name`     char(255) default '',
          `storno`   tinyint(3) unsigned default 0,

          `p_idgroup`    char(24) DEFAULT '0',
          `p_section`  tinyint(1) unsigned DEFAULT 1,
          `p_cena`     double(8,2) default 0,
          `p_sheme`    tinyint(3) unsigned default 0,
          `p_max_skid` double(8,2) default 0,
          `p_real`     tinyint(3) unsigned default 0,
          `p_type`     tinyint(3) unsigned default 0,
          `p_alco`     tinyint(3) unsigned default 0,
          `p_minprice` double(8,2) default 0,
          `p_maxprice` double(8,2) default 0,

          `multiprice` tinyint(3) unsigned default 0,
          `paramf1`  double(8,2) DEFAULT 0,
          `paramf2`  double(7,3) DEFAULT 1,
          `paramf3`  double(8,2) DEFAULT 0,
          `mark`     char(6) default '',
          `dcount`   double(7,3),

          `discount`  double(8,2) DEFAULT 0,
          `bonus`  double(8,2) DEFAULT 0,
          `bonus_discount`  double(8,2) default 0,
          `p_litrag` double(8,4) default 0,
          `ean`      char(24) default '',
          `barcode`  char(68) default '',
          `p_shk`    char(13) default '',
          `discount_pos`    double(8,2) default 0,
          `bonus_pos`       double(8,2) default 0,
          `nbox`    tinyint(2) default 0,
          PRIMARY KEY (`iduser`,`idcheck`,`id`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _where(self,iduser,idcheck):
        return "iduser=%d and idcheck=%d" % (iduser,idcheck)

    def _wherepos(self,iduser,idcheck,id):
        return "iduser=%d and idcheck=%d and id=%d" % (iduser,idcheck,id)

    def _clear(self,iduser,idcheck):
        return self.query_delete(self._where(iduser,idcheck))

    def _find_barcode(self,iduser,idcheck,barcode):
        return self.query_all_select()+" where "+self._where(iduser,idcheck)+" and barcode='%s'" % barcode

    def _get(self,iduser,idcheck,id):
        return self.query_all_select()+" where "+self._wherepos(iduser,idcheck,id)

    def _gets(self,iduser,idcheck):
        return self.query_all_select()+" where "+self._where(iduser,idcheck)

    def _add(self,iduser,idcheck,struct):
        dt = my.curdate2my()
        tm = my.curtime2my()
        struct["date"] = dt
        struct["time"] = tm 
        struct["iduser"]=iduser
        struct["idcheck"]=idcheck
        return self.query_insert(struct)

    def _upd(self,iduser,idcheck,id,struct):
        return self.query_update(struct)+" where "+self._wherepos(iduser,idcheck,id)

    def _updid(self,iduser,idcheck,id,iduser2=None):
        struct={'idcheck':id,};
        if iduser2!=None:
            struct['iduser']=iduser2
        return self.query_update(struct)+" where "+self._where(iduser,idcheck)

    def _del(self,iduser,id):
        return self.query_delete("iduser=%d and id=%d" % (iduser,id))

    def _dels(self,iduser,idcheck,_list):
        return self.query_delete("%s and id in (%s)" % (self._where(iduser,idcheck),_list))

    def _upds(self,iduser,idcheck,struct):
        return self.query_update(struct) + "where iduser=%s and idcheck=%s" % (iduser,idcheck)

class tb_price(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','s')
        self.addfield('shk','s')
        self.addfield('name','s')
        self.addfield('litrag','f')

        self.addfield('cena','f')
        self.addfield('ostatok','f')
        self.addfield('sheme','d')
        self.addfield('real','d')

        self.addfield('section','d')
        self.addfield('max_skid','f')
        self.addfield('type','d')
        self.addfield('alco','d')

        self.addfield('minprice','f')
        self.addfield('maxprice','f')
        self.addfield('reserved2','s')
        self.addfield('idgroup','s')
        self.addfield('istov','d')

    def _create(self):
        q="""
      CREATE TABLE `%s` (
      `id`          varchar(24) NOT NULL DEFAULT '',
      `shk`         varchar(13) DEFAULT NULL,
      `name`        varchar(255) NOT NULL,
      `litrag`      double(15,4) DEFAULT 0,

      `cena`        double(15,2) unsigned NOT NULL DEFAULT '0.00',
      `ostatok`     double(17,3) unsigned NOT NULL DEFAULT '0.000',
      `sheme`       tinyint(1) NOT NULL DEFAULT '0',
      `real`        tinyint(1) NOT NULL DEFAULT '0',

      `section`     smallint(2) NOT NULL DEFAULT '0',
      `max_skid`    double(5,2) NOT NULL DEFAULT '0.0',
      `type`        tinyint(1) NOT NULL DEFAULT '0',
      `alco`        tinyint(1) NOT NULL DEFAULT '0',

      `minprice`    double(15,2) NOT NULL DEFAULT '0.00',
      `maxprice`    double(15,2) NOT NULL DEFAULT '0.00',

      `reserved2`   varchar(24) DEFAULT NULL,
      `idgroup`     varchar(24) DEFAULT NULL,
      `istov`       tinyint(1) NOT NULL DEFAULT '0',

      PRIMARY KEY (`id`),
      KEY `name` (`name`,`shk`),
      KEY `idgroup` (`idgroup`,`id`),
      KEY `section` (`section`,`id`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _get_in_list(self,_list):
        return self.query_all_select()+" where id in (%s)" % _list

    def _get_group(self,parent):
        return self.query_all_select()+" where idgroup='%s' order by istov,name" % parent

    def _get(self,code):
        if code!=None:
            _if=" where id='%s'" % code
        else:
            _if=""
        return self.query_all_select()+_if

    def _find_shk(self,shk):
        return self.query_all_select()+"where shk='%s'" % (shk)

    def _add(self,values):
        struct=self.set_all_values(values)
        return self.query_insert(struct)

    def _upd(self,code,struct):
        return self.query_update(struct)+" where id='%s'" % code

    def _upd_grow(self,code,ost):
        return "update %s set ostatok=ostatok+%s where id='%s'" % (self.tablename,ost,code)

class tb_price_shk(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('shk','s')
        self.addfield('name','s')
        self.addfield('cena','f')
        self.addfield('koef','f')

    def _create(self):
        q="""
      CREATE TABLE `%s` (
      `id`          varchar(24) NOT NULL DEFAULT '',
      `shk` varchar(13) NOT NULL DEFAULT '',
      `name` varchar(255) NOT NULL,
      `cena` double(15,2) unsigned NOT NULL DEFAULT '0.00',
      `koef` double(17,3) unsigned NOT NULL DEFAULT '0.000',
      PRIMARY KEY (`id`,`shk`,`cena`),
      KEY `shk` (`shk`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename

        return q

    def _get(self,code,shk=None):
        if shk!=None:
            _if=" and shk='%s'" % shk
        else:
            _if=""
        return self.query_all_select()+"where id='%s' %s group by cena order by cena desc" % (code,_if)

    def _find_shk(self,shk):
        return self.query_all_select()+"where shk='%s'" % (shk)

    def _add(self,values):
        struct=self.set_all_values(values)
        return self.query_insert(struct)

    def _upd(self,code,shk,values):
        struct = self.set_values(['name','cena','koef'],values)
        return self.query_update(struct)+" where id='%s' and shk='%s'" % (code,shk)

class tb_discount(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('number','s')
        self.addfield('name','s')
        self.addfield('text','s')
        self.addfield('isclose','d')
        self.addfield('type','d')
        self.addfield('procent','d')

    def _create(self):
        q="""
      CREATE TABLE `%s` (
      `number` varchar(24) NOT NULL,
      `name` varchar(100) DEFAULT 'DISCOUNT CARD',
      `text` varchar(30) DEFAULT 'discount',
      `isclose` tinyint(1) NOT NULL DEFAULT '0',
      `type` tinyint(1) NOT NULL DEFAULT '0',
      `procent` double(5,2) NOT NULL DEFAULT '20.00',
      PRIMARY KEY (`number`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename

        return q

    def _get(self,code):
        return self.query_all_select()+"where number='%s' and isclose=0" % (code)

class tb_types(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('pref','s')
        self.addfield('id','d')
        self.addfield('name','s')

        self.record_add = self.fieldsorder 

    def _create(self):
        q="""create table `%s` (
        `pref`  char(8) default '',
        `id`    int(4),
        `name`  char(64) default '',
        primary key (`pref`,`id`),
        unique  key `name` (`name`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q


    def _add(self,arrvalues):
        struct = self.set_values(self.record_add,arrvalues)
        return self.query_insert(struct)

    def _get(self,pref):
        return self.query_select(['pref','id','name'],"pref='%s' order by name" % pref)

class tb_Zet(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('idplace','d')
        self.addfield('nkassa','d')

        self.addfield('begin_date','D')
        self.addfield('begin_time','t')
        self.addfield('end_date','D')
        self.addfield('end_time','t')
        self.addfield('date','D')

        self.addfield('begin_ncheck','f')
        self.addfield('end_ncheck','f')

        self.addfield('summa_ret','f')
        self.addfield('c_sale','d')
        self.addfield('c_return','d')
        self.addfield('c_error','d')
        self.addfield('c_cancel','d')

        self.addfield('summa','f')
        self.addfield('summa_ret','f')
        self.addfield('summa_nal','f')
        self.addfield('summa_bnal','f')

        self.addfield('discount','f')
        self.addfield('bonus','f')
        self.addfield('bonus_discount','f')

        self.addfield('number','d')
        self.addfield('vir','f')
        self.addfield('up','d')

        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id`          int(4) unsigned NOT NULL AUTO_INCREMENT,
          `idplace`     int(4) default 1,
          `nkassa`      tinyint(1) default 1,

          `begin_date`  date,
          `begin_time`  time,
          `end_date`    date,
          `end_time`    time,
          `date`        date,

          `begin_ncheck` int(4),
          `end_ncheck` int(4),

          `c_sale`     int(4) default 0,
          `c_return`   int(4) default 0,
          `c_error`    int(4) default 0,
          `c_cancel`   int(4) default 0,

          `summa`      double(8,2) default 0,
          `summa_ret`  double(8,2) default 0,
          `summa_nal`  double(8,2) default 0,
          `summa_bnal` double(8,2) default 0,

          `discount`   double(8,2) default 0,
          `bonus`      double(8,2) default 0,
          `bonus_discount`  double(8,2) default 0,
          `number`     int(4) default 0,
          `vir`        double(8,2) default 0,
          `up`      tinyint(1) default 0,

          PRIMARY KEY (`id`),
          KEY `pl` (`idplace`,`nkassa`,`id`),
          KEY `dt` (`idplace`,`nkassa`,`date`),
          KEY `up` (`idplace`,`nkassa`,`up`,`date`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _last(self,idplace,nkassa):
        q=self.query_all_select()+"where idplace=%d and nkassa=%d order by end_date desc,end_time desc limit 1" % (idplace,nkassa)
        #print q
        return q

    def _add(self,struct):
        return self.query_insert(struct)

    def _gets(self,dt1,dt2,up=None):
        s=""
        a=""
        if up!=None:
            s+="up=%d" % up
            a=" and "
        if dt1!=None:
            s+=a+"date>='%s'" % dt1
            a=" and "
        if dt2!=None:
            s+=a+"date<='%s'" % dt2
        if s!="":
            s=" where "+s
        return self.query_all_select()+s+" order by idplace,nkassa,id"

    def _get(self,idplace,nkassa,id):
        return self.query_all_select()+" where idplace=%d and nkassa=%d and id=%d" % (idplace,nkassa,id)

    def _upd(self,id,struct):
        return self.query_update(struct)+" where id='%s'" % (id)

class tb_Zet_cont(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('idhd','d')

        self.addfield('section','d')
        self.addfield('idgroup','d')
        self.addfield('code','s')
        self.addfield('alco','d')

        self.addfield('paramf1','f')
        self.addfield('paramf2','f')
        self.addfield('paramf3','f')

        self.addfield('discount','f')
        self.addfield('bonus','f')
        self.addfield('bonus_discount','f')

        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id`          int(4) unsigned NOT NULL AUTO_INCREMENT,
          `idhd`        int(4) default 1,

          `section`    tinyint(1) default 0,
          `idgroup`    int(4) default 0,
          `code`       varchar(24) default 0,
          `alco`       tinyint(1) default 0,

          `paramf1`    double(8,2) default 0,
          `paramf2`    double(8,3) default 0,
          `paramf3`    double(8,2) default 0,

          `discount`   double(8,2) default 0,
          `bonus`      double(8,2) default 0,
          `bonus_discount`  double(8,2) default 0,

          PRIMARY KEY (`idhd`,`id`),
          KEY `dt` (`idhd`,`code`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _add(self,struct):
        return self.query_insert(struct)

    def _dels(self,id):
        return self.query_delete("idhd=%d" % id)

    def _get(self,idhd):
        return self.query_all_select()+" where idhd=%d" % idhd

    def _gethtml(self,idhd):
        self.query_all_select()
        return "select ct.*,pr.name from %s as ct,tb_price as pr where idhd=%d and pr.id=ct.code" % (self.tablename,idhd)

class tb_egais_places(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('ClientRegId','s')
        self.addfield('INN','s')
        self.addfield('KPP','s')
        self.addfield('FullName','s')
        self.addfield('ShortName','s')
        self.addfield('description','s')
        self.addfield('RegionCode','s')
        self.addfield('Country','s')
        self.addfield('city','s')
        self.addfield('street','s')
        self.addfield('house','s')
        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id` int(12) NOT NULL AUTO_INCREMENT,
          `ClientRegId` char(40) DEFAULT '',
          `INN`         char(20) DEFAULT '',
          `KPP`         char(20) DEFAULT '',
          `FullName`    char(255) DEFAULT '',
          `ShortName`   char(255) DEFAULT '',
          `description` char(255) DEFAULT '',
          `RegionCode`  char(5) DEFAULT '42',
          `Country`     char(5) DEFAULT '643',
          `city`        char(40) DEFAULT '',
          `street`      char(40) DEFAULT '',
          `house`       char(40) DEFAULT '',
          PRIMARY KEY (`id`),
          KEY `idd` (`inn`,`kpp`),
          KEY `fsrar` (`ClientRegId`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """ % self.tablename
        return q

    def _add(self,struct):
        return self.query_insert(struct)


class tb_egais_docs_hd(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('type','d')
        self.addfield('puttime','t')
        self.addfield('status','d')
        self.addfield('user','s')

        self.addfield('xml_doc','s')
        self.addfield('xml_ticket','s')
        self.addfield('xml_inform','s')
        self.addfield('xml_answer','s')

        self.addfield('url','s')
        self.addfield('reply_id','s')
        self.addfield('ns_FSRAR_ID','s')
        self.addfield('ns_typedoc','s')

        self.addfield('wb_Identity','s')
        self.addfield('wb_NUMBER','s')

        self.addfield('wb_Date','D')
        self.addfield('wb_ShippingDate','D')
        self.addfield('wb_Type','s')
        self.addfield('wb_UnitType','s')

        self.addfield('send_INN','s')
        self.addfield('send_KPP','s')
        self.addfield('send_ShortName','s')
        self.addfield('send_RegId','s')

        self.addfield('recv_INN','s')
        self.addfield('recv_KPP','s')
        self.addfield('recv_ShortName','s')
        self.addfield('recv_RegId','s')
        self.addfield('tc_RegId','s')
        self.addfield('wt_IsConfirm','s')
        self.addfield('tc_OperationName','s')
        self.addfield('tc_OperationResult','s')
        self.addfield('answer','s')

        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id` int(12) NOT NULL AUTO_INCREMENT,
          `type` tinyint(1) default 0,
          `puttime` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
          `status` smallint(1) DEFAULT '0',
          `user` char(20) DEFAULT 'robot',

          `xml_doc`    mediumtext,
          `xml_ticket` mediumtext,
          `xml_inform` mediumtext,
          `xml_answer` mediumtext,

          `url`         char(255) DEFAULT '',
          `reply_id`    char(255) DEFAULT '',

          `ns_FSRAR_ID` char(40) DEFAULT '',
          `ns_typedoc`  char(40) DEFAULT '',

          `wb_Identity` char(40) DEFAULT '',
          `wb_NUMBER`   char(30) DEFAULT '',

          `wb_Date`         date DEFAULT NULL,
          `wb_ShippingDate` date DEFAULT NULL,

          `wb_Type`         char(30) DEFAULT NULL,
          `wb_UnitType`     char(30) DEFAULT NULL,

          `send_INN`        char(20) DEFAULT NULL,
          `send_KPP`        char(20) DEFAULT NULL,
          `send_SHORTNAME`  char(255) DEFAULT NULL,
          `send_RegId`      char(30) DEFAULT '',

          `recv_INN`        char(20) DEFAULT NULL,
          `recv_KPP`        char(20) DEFAULT NULL,
          `recv_SHORTNAME`  char(255) DEFAULT NULL,
          `recv_RegId`      char(30) DEFAULT '',
          
          `tc_RegId`            char(40) DEFAULT '',
          `wt_IsConfirm`        char(40) DEFAULT '',
          `tc_OperationName`    char(40) DEFAULT '',
          `tc_OperationResult`  char(40) DEFAULT '',

          `answer`      char(20) DEFAULT NULL,
          PRIMARY KEY (`id`),
          KEY `news` (`type`,`status`,`wb_Date`,`recv_RegId`,`send_RegId`),
          KEY `num`  (`type`,`recv_RegId`,`send_RegId`,`wb_NUMBER`),
          KEY `postav`  (`type`,`send_RegId`,`wb_NUMBER`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        
        return q

    def _del(self,id):
        return self.query_delete("id=%s" % id)

    def _get(self,id):
        return self.query_all_select()+" where id=%d" % id

    def _add(self,struct):
        return self.query_insert(struct)

    def _upd(self,id,struct):
        return self.query_update(struct)+" where id=%d" % (id)

    def _find(self,_type,recv_RegId,send_RegId,wb_NUMBER):
        #return self.query_all_select()+" where type=%d and recv_RegId='%s' and send_RegId='%s' and wb_NUMBER='%s'" % (_type,recv_RegId,send_RegId,wb_NUMBER)
        if _type==None:
            _type="type<>-1"
        else:
            _type="type=%s" % _type

        return self.query_all_select()+" where %s and recv_RegId='%s' and send_RegId='%s' and wb_NUMBER='%s'" % (_type,recv_RegId,send_RegId,wb_NUMBER)

    def _find_replyId(self,reply_id):
        #print self.query_all_select()+" where reply_id='%s'" % (reply_id)
        return self.query_all_select()+" where reply_id='%s'" % (reply_id)

    def _find_ttn(self,ttn):
        return self.query_all_select()+" where tc_RegId='%s'" % (ttn)

    def _get_postav(self):
        return "select send_RegId,send_SHORTNAME from %s group by send_RegId"  % (self.tablename)

    def _get_docs(self,_type,status,postav,dt1,dt2):
        if status==None or status==0:
            st="status<>0"
        else:
            st="status=%d" % status
        if postav!=None:
            post=" and send_RegId='%s'" % postav
        else:
            post=""
        dt=""
        if dt1!=None:
            dt+=" and wb_date>='%s'" % dt1
        if dt2!=None:
            dt+=" and wb_date<='%s'" % dt2
        tp=" and type=%s" % _type
        #print self.query_all_select()+" where %s %s %s %s order by id desc limit 30"  % (st,post,dt,tp)
        return self.query_all_select()+" where %s %s %s %s order by id desc limit 30"  % (st,post,dt,tp)

class tb_egais_docs_ct(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('iddoc','d')
        self.addfield('wb_Identity','s')

        self.addfield('pref_Type','s')
        self.addfield('pref_ShortName','s')
        self.addfield('pref_AlcCode','s')
        self.addfield('pref_Capacity','f')
        self.addfield('pref_AlcVolume','f')
        self.addfield('pref_ProductVCode','s')
        self.addfield('oref_ClientRegId','s')
        self.addfield('oref_INN','s')
        self.addfield('oref_KPP','s')
        self.addfield('oref_ShortName','s')
        self.addfield('wb_Quantity','f')
        self.addfield('wb_Price','f')
        self.addfield('wb_Pack_ID','s')
        self.addfield('wb_Party','s')
        self.addfield('pref_RegId','s')
        self.addfield('pref_BRegId','s')
        self.addfield('wbr_InformBRegId','s')
        self.addfield('real_Quantity','f')

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id` int(12) NOT NULL AUTO_INCREMENT,
          `iddoc`       int(12)  DEFAULT NULL,
          `wb_Identity` char(30) DEFAULT NULL,
          
          `pref_Type`       char(20) DEFAULT NULL,
          `pref_ShortName`  char(255) DEFAULT NULL,
          `pref_AlcCode`    char(30) DEFAULT NULL,
          `pref_Capacity`   decimal(10,4) DEFAULT NULL,
          `pref_AlcVolume`  decimal(10,3) DEFAULT NULL,
          `pref_ProductVCode` char(10) DEFAULT NULL,

          `oref_ClientRegId` char(20) DEFAULT NULL,
          `oref_INN` char(20) DEFAULT NULL,
          `oref_KPP` char(20) DEFAULT NULL,
          `oref_ShortName` char(255) DEFAULT NULL,

          `wb_Quantity` decimal(12,4) DEFAULT NULL,
          `wb_Price`    decimal(10,2) DEFAULT NULL,
          `wb_Pack_ID`  char(20) DEFAULT NULL,
          `wb_Party`    char(40) DEFAULT NULL,

          `pref_RegId`  char(40) DEFAULT NULL,
          `pref_BRegId` char(40) DEFAULT NULL,
          `wbr_InformBRegId` char(40) DEFAULT NULL,

          `real_Quantity` decimal(12,4) DEFAULT NULL,
          PRIMARY KEY (`iddoc`,`id`),
          KEY `idd` (`iddoc`,`wb_Identity`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """ % self.tablename
        return q

    def _del(self,id):
        return self.query_delete("iddoc=%s" % id)

    def _add(self,struct):
        print self.query_insert(struct)
        return self.query_insert(struct)

    def _upd(self,iddoc,id,struct):
        return self.query_update(struct)+" where iddoc=%d and id='%s'" % (iddoc,id)

    def _updId(self,iddoc,id,struct):
        return self.query_update(struct)+" where iddoc=%d and wb_Identity='%s'" % (iddoc,id)

    def _get(self,id):
        return self.query_all_select()+" where iddoc=%d" % id

    def _getpos(self,idd,id):
        return self.query_all_select()+" where iddoc=%d and id=%d" % (idd,id)

class tb_egais_ostat(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('rst_InformARegId','s')
        self.addfield('rst_InformBRegId','s')
        self.addfield('rst_Quantity','f')
        self.addfield('pref_FullName','s')
        self.addfield('pref_AlcCode','s')
        self.addfield('pref_AlcVolume','f')
        self.addfield('pref_ProductVCode','s')
        self.addfield('oref_ClientRegId','s')
        self.addfield('oref_INN','s')
        self.addfield('oref_KPP','s')
        self.addfield('oref_ShortName','s')
        self.addfield('oref_FullName','s')
        self.addfield('oref_Country','s')
        self.addfield('oref_RegionCode','s')
        self.addfield('oref_description','s')
        self.addfield('pref_Capacity','s')
        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id` int(12) NOT NULL AUTO_INCREMENT,
          `rst_InformARegId` char(40) DEFAULT NULL,
          `rst_InformBRegId` char(40) DEFAULT NULL,
          `rst_Quantity` decimal(12,4) DEFAULT NULL,
          `pref_FullName`  char(255) DEFAULT NULL,
          `pref_AlcCode`    char(30) DEFAULT NULL,
          `pref_AlcVolume`  decimal(10,3) DEFAULT NULL,
          `pref_ProductVCode` char(10) DEFAULT NULL,

          `oref_ClientRegId` char(20) DEFAULT NULL,
          `oref_INN` char(20) DEFAULT NULL,
          `oref_KPP` char(20) DEFAULT NULL,
          `oref_ShortName` char(255) DEFAULT NULL,
          `oref_FullName` char(255) DEFAULT NULL,
          `oref_Country` char(10) DEFAULT "643",
          `oref_RegionCode` char(10) DEFAULT "42",
          `oref_description` char(255) DEFAULT NULL,
          `pref_Capacity` char(20) DEFAULT NULL,


          PRIMARY KEY (`id`),
          KEY `idd` (`pref_AlcCode`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """ % self.tablename
        return q

    def _add(self,struct):
        return self.query_insert(struct)

    def _gets(self):
        return self.query_all_select()+" order by oref_ClientRegId,pref_AlcCode"

    def _get(self,id):
        return self.query_all_select()+" where id=%d" % id

    def _find(self,alccode):
        return self.query_all_select()+" where pref_AlcCode=%s" % (alccodea)

class tb_egais_docs_need(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('ttn_WbRegID','s')
        self.addfield('ttn_ttnNumber','s')
        self.addfield('ttn_ttnDate','D')
        self.addfield('ttn_Shipper','s')
        self.record_add = self.fieldsorder[1:] 

    def _create(self):
        q="""
        CREATE TABLE `%s` (
          `id` int(12) NOT NULL AUTO_INCREMENT,
          `ttn_WbRegID` char(40) DEFAULT NULL,
          `ttn_ttnNumber` char(40) DEFAULT NULL,
          `ttn_ttnDate` date default NULL,
          `ttn_Shipper` char(40) DEFAULT NULL,
          PRIMARY KEY (`id`),
          KEY `idd` (`ttn_WbRegID`)
        ) ENGINE=MyISAM DEFAULT CHARSET=utf8
        """ % self.tablename
        return q

    def _add(self,struct):
        return self.query_insert(struct)

    def _gets(self):
        self.query_all_select()
        q="select *,"+\
        "(select status from tb_egais_docs_hd as hd where ttn_WbRegID=hd.tc_RegId)as d_status"+\
        " from tb_egais_docs_need order by ttn_ttnDate desc"
        self.query_fields.append('d_status')
        return q

class tb_actions_hd(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('name','s')
        self.addfield('dt1','D')
        self.addfield('dt2','D')
        self.addfield('tm1','t')
        self.addfield('tm2','t')
        self.addfield('daysweek','s')
        self.addfield('_if','s')
        self.addfield('_then','s')
        self.record_add = self.fieldsorder[1:]

    def _create(self):
        q="""
      CREATE TABLE `%s` (
      `id`          int(4) AUTO_INCREMENT,
      `name`        varchar(255) NOT NULL,
      `dt1`         date,
      `dt2`         date,
      `tm1`         time,
      `tm2`         time,
      `daysweek`    varchar(8) default '0000000',
      `_if`         mediumtext default '',
      `_then`       mediumtext default '',
      PRIMARY KEY (`id`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _clear(self):
        return self.empty_all_values()

    def _gets(self):
        curd=my.curdate2my()
        curt=my.curtime2my()
        return self.query_all_select()+" where dt1<='%s' and dt2>='%s' and tm1<='%s' and tm2>='%s' order by name" % (curd,curd,curt,curt)

    def _get(self,id):
        return self.query_all_select()+" where id=%d" % (idreg,id)

    def _find(self,idreg,name):
        return self.query_all_select()+" where idreg=%d and name='%s'" % (idreg,name)

    def _add(self,struct):
        return self.query_insert(struct)

class tb_tlist(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('name','s')
        self.addfield('idt','d')
        self.record_add = self.fieldsorder

    def _create(self):
        q="""
      CREATE TABLE `%s` (
      `name`        varchar(255) NOT NULL,
      `idt`         int(4),
      PRIMARY KEY (`name`,`idt`)
    ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _clear(self):
        return self.empty_all_values()

    def _gets(self):
        return self.query_all_select()

    def _get(self,name):
        return self.query_all_select()+" where name='%s'" % (name)

    def _add(self,name,idt):
        struct = {'name':name,'idt':idt}
        return self.query_insert(struct)

class tb_boxes_hd(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('idhd','d')
        self.addfield('status','d')
        self.addfield('counts','d')
        self.addfield('opened','d')
        self.addfield('iduser','d')
        self.addfield('dt','D')
        self.addfield('tm','t')

    def _create(self):
        q="""create table `%s` (
        `id`      smallint(2) unsigned NOT NULL,
        `idhd`    smallint(2) default 0,
        `status`  tinyint(1)  default 0,
        `counts`  tinyint(1)  default 0,
        `opened`  tinyint(1)  default 0,
        `iduser`  tinyint(1)  default 0,
        `dt`      date,
        `tm`      time,
        primary key (`id`),
        key `status` (`status`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _gets(self):
        self.query_all_select()
        self.query_fields.append("d_sub")
        self.query_fields.append("d_counts")
        return "select *,(select count(*) from %s as b where b.idhd=a.id) as d_sub,\
        (select count(*) from tb_boxes_ct as b where b.idhd=a.id and b.storno=0) as d_counts\
        from %s as a" % (self.tablename,self.tablename)
        #return self.query_all_select()

    def _getid(self,id):
        self.query_all_select()
        self.query_fields.append("d_sub")
        self.query_fields.append("d_counts")
        return "select *,(select count(*) from %s as b where b.idhd=a.id) as d_sub,\
        (select count(*) from tb_boxes_ct as b where b.idhd=a.id and b.storno=0) as d_counts\
        from %s as a where id=%s" % (self.tablename,self.tablename,id)

class tb_boxes_ct(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('idhd','d')
        self.addfield('id','d')
        self.addfield('code','d')
        self.addfield('count','f')
        self.addfield('storno','d')

    def _create(self):
        q="""create table `%s` (
        `idhd`    smallint(2) default 0,
        `id`      int(4) AUTO_INCREMENT,
        `code`    int(4),
        `count`   decimal(8,3)  default 1,
        `storno`  tinyint(1) default 0,
        primary key (`idhd`,`id`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _gethd(self,idhd):
        self.query_all_select()
        self.query_fields.append("d_price")
        return "select ct.*,(select name from tb_price as p where p.id=ct.code) as d_price from %s as ct where idhd=%s" % (self.tablename,idhd)

