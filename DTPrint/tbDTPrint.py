#!/usr/bin/python
# -*- coding: utf-8
# version 1.000
import my
from md5 import md5

class tb_sets(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('name','s')
        self.addfield('value','s')

    def _create(self):
        q="""create table `%s` (
        `id`    int(4) unsigned NOT NULL AUTO_INCREMENT,
        `name`  char(64) default 'simple',
        `value` char(255) default '',
        primary key (`id`),
        unique  key `name` (`name`) ) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _get(self,name):
        return self.query_select(['value']," where name='%s'" % name)

    def _getall(self):
        return self.query_all_select()

    def _add(self,arrvalues):
        struct = self.set_values(['name','value'],arrvalues)
        return self.query_insert(struct)

    def _upd(self,name,value):
        struct = self.set_values(['value'],[value])
        return self.query_update(struct)+" where name='%s'" % name

class tb_logs(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('ip','s')
        self.addfield('user','s')
        self.addfield('cmd','s')
        self.addfield('url','s')
        self.addfield('xml','s')
        self.addfield('puttime','D')
        self.addfield('result','d')

    def _create(self):
        q="""create table `%s` (
        `id`      int(4) unsigned NOT NULL AUTO_INCREMENT,
        `ip`      char(32) default '',
        `user`    char(32) default '',
        `cmd`     char(32) default '',
        `url`     char(200) default '',
        `puttime` timestamp,
        `xml`  mediumtext,
        `result` int(4) default 0,
        primary key (`id`),
        key `ustm` (`user`,`puttime`),
        key `pttm` (`puttime`)) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _get(self,dt1,dt2,ip,user):
        def add_where(ifs):
            if self.where=='':
                self.where+=" where %s" % ifs
            else:
                self.where+=" and %s" % ifs
        self.where=""
        if dt1!='':
            add_where("date(puttime)>='%s'" % dt1)
        if dt2!='':
            add_where("date(puttime)<='%s'" % dt2)
        if ip!='':
            add_where("ip='%s'" % ip)
        if user!='':
            add_where("user='%s'" % user)

        return self.query_all_select()+self.where+" order by puttime"

    def _add(self,arrvalues):
        struct = self.set_values(['ip','user','cmd','url','xml','result'],arrvalues)
        return self.query_insert(struct)

class tb_printers(my.table):
    def __init__ (self,dbname):
        my.table.__init__(self,dbname)
        self.addfield('id','d')
        self.addfield('name','s')
        self.addfield('vendor','s')
        self.addfield('interface','d')
        self.addfield('byte1','s')
        self.addfield('byte2','s')
        self.addfield('id_vendor','s')
        self.addfield('id_product','s')
        self.addfield('type_device','d')
        self.addfield('type_connect','d')
        self.addfield('device','s')
        self.addfield('address','s')
        self.addfield('port','d')
        self.addfield('speed','d')
        self.addfield('charset_driver','s')
        self.addfield('charset_device','d')
        self.addfield('isoff','d')
        self.addfield('width','d')
        self.addfield('dpi','d')
        self.addfield('usr_pass','s')
        self.addfield('adm_pass','s')
        self.addfield('description','s')
        self.fields_upd=['name','vendor','interface','byte1','byte2','id_vendor','id_product','type_device','type_connect','device','address','port','charset_driver','charset_device','isoff','width','dpi','description','speed','usr_pass','adm_pass']

    def _create(self):
        q="""create table `%s` (
        `id`      int(4) unsigned NOT NULL AUTO_INCREMENT,
        `name`    char(32) default 'default',
        `vendor`  char(255) default 'none',
        `byte1` char(4) default '0x0',
        `byte2` char(4) default '0x0',
        `id_vendor` char(4) default '0x0',
        `id_product` char(4) default '0x0',
        `type_device` int(4) default 0,
        `type_connect` int(4) default 1,
        `address` char(20) default 'localhost',
        `device` char(255) default '',
        `port` int(4) default 9600,
        `speed` int(4) default 115200,
        `charset_driver` char(64) default 'cp866',
        `charset_device` int(4) default 17,
        `interface` smallint(1) default 0,
        `isoff` smallint(1) default 1,
        `usr_pass`   char(4) default '0000',
        `adm_pass`   char(4) default '0030',
        `dpi`   int(4) default 0,
        `width` int(4) default 0,
        `description` char(255) default '',
        primary key (`id`)) ENGINE=MyISAM DEFAULT CHARSET=utf8""" % self.tablename
        return q

    def _get(self,id=0,name=''):
        def add_where(ifs):
            if self.where=='':
                self.where+=" where %s" % ifs
            else:
                self.where+=" and %s" % ifs
        self.where=""
        if id!=0:
            add_where("id=%d" % id)
        if name!='':
            add_where("name='%s'" % name)
        return self.query_all_select()+self.where+" order by id"

    def _get_names(self):
        return "select name from "+self.tablename+" order by name"

    def _add(self,post):
        if type(post)!=dict:
            struct=self.post2struct(post,self.fields_upd)
        else:
            struct=post
        return self.query_insert(struct)

    def _newid(self,id,newid):
        struct={'id':newid}
        return self.query_update(struct)+" where id=%d" % id

    def _upd(self,id,post):
        if type(post)!=dict:
            struct=self.post2struct(post,self.fields_upd)
        else:
            struct=post
        if type(id)==int:
            w=" where id=%d" % id
        else:
            w=" where name='%s'" % id
        return self.query_update(struct)+w

    def _del(self,id=0,name=""):
        if id!=0:
            return "delete from %s where id=%d" % (self.tablename,id)
        else:
            return "delete from %s where name='%s'" % (self.tablename,name)


    def _upd_usr(self,id,arrvalues):
        struct = self.set_values(['name','type_device','type_connect','address','port','charset_driver','charset_device','description'],arrvalues)
        return self.query_update(struct)+" where id=%d" % id

    def _upd_dev(self,id,arrvalues):
        struct = self.set_values(['vendor','id_vendor','id_product','byte1','byte2'],arrvalues)
        return self.query_update(struct)+" where id=%d" % id
