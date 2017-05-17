#!/usr/bin/python
# -*- coding: utf-8
import string
import copy
import time
from datetime import datetime
import MySQLdb


Q_LASTID="select last_insert_id()"

def mysql_timestamp():
    return datetime.now().strftime(format="%Y-%m-%d %H:%M:%S")
def mydt2time(d,t):
    struct_time=time.strptime(d+"_"+t,"%Y-%m-%d_%H:%M:%S")
    return time.mktime(struct_time)
def mydt2normdt(d):
    d=str(d)
    a=d.split('-')
    return a[2]+'.'+a[1]+'.'+a[0]
def curdate2my():
    t=time.localtime()
    return str(t.tm_year)+'-'+str(t.tm_mon).rjust(2,"0")+'-'+str(t.tm_mday).rjust(2,"0")
def curtime2my():
    t=time.localtime()
    return str(t.tm_hour).rjust(2,"0")+':'+str(t.tm_min).rjust(2,"0")+':'+str(t.tm_sec).rjust(2,"0")

def del_empty_hash(h,k):
    if h.has_key(k):
        if h[k]=='':
            del h[k]
def ch_hash(h,k,v):
    if h.has_key(k):
        h[k]=v

class table:
    def __init__ (self,dbname):
        self.tablename=dbname
        self.field_list={}
        self.field_value={}
        self.fieldsorder=[]
        self.defaults={'s':'','d':0,'f':0,}

    def addfield(self,fn,ft):
        self.field_list[fn]=ft
        self.fieldsorder.append(fn)

    def number_field(self,field_name):
        return self.fieldsorder.index(field_name)

    def empty (self,v):
        if self.defaults.has_key(v):
            r=self.defaults[v]
        else:
            r=''
        return r

    def set_values (self,fields,valuesorder):
        field_value={}
        i=0
        for k in fields:
            if self.field_list[k] in ('d','f') and valuesorder[i]=="":
                valuesorder[i]="0"
            field_value[k]=valuesorder[i]
            i=i+1
        return field_value

    def set_all_values (self,valuesorder):
        field_value=self.field_list.copy()
        i=0
        for k in self.fieldsorder:
            if field_value[k] in ('d','f') and valuesorder[i]=="":
                valuesorder[i]="0"
            field_value[k]=valuesorder[i]
            i=i+1
        return field_value

    def empty_all_values (self,flist=None):
        field_value=self.field_list.copy()
        if flist==None:
            flist = field_value.keys()
        for k in flist:
            field_value[k]=self.empty(field_value[k])
        return field_value

    def query_select (self,field_list,where=""):
        self.query_fields=copy.copy(field_list)
        if where!="":
            where="where "+where
        fd=[]
        for v in field_list:
            fd.append("`%s`" % v)
        fields=",".join(fd)
        s="select %s from %s %s" % (fields,self.tablename,where)
        return s
    
    def query_all_select (self):
        self.query_fields=self.fieldsorder
        return self.query_select(self.fieldsorder)

    def result2value(self,data,key,decode=True,encode=False,tostr=False,dttm2str=True):
        if key in self.query_fields:
            r=data[self.query_fields.index(key)]
            if self.field_list.has_key(key):
                _type=self.field_list[key]
            else:
                _type=key[0]
            if tostr and _type != 's':
                r=str(r)
            if dttm2str and _type in ('D','t'):
                r=str(r)
            if r!=None:
                if decode and type(r)!=unicode and _type=='s':
                    r=r.decode("utf8")
                elif type(r)==unicode and _type=='s' and encode:
                    r=r.encode("utf8")
                    #print "%s=%s %s %s" % (key,self.field_list[key],type(r),r)
            return r
        else:
            print "error.not found key"
            return '0'

    def result2values(self,data,decode=True,encode=False,tostr=False,dttm2str=True):
        values={}
        for key in self.query_fields:
            values[key]=self.result2value(data,key,decode=decode,encode=encode,tostr=tostr,dttm2str=dttm2str)
        return values

    def post2struct(self,h,fields):
        result={}
        for key in fields:
            if h.has_key(key):
                r=h[key].value
                if type(r)==unicode:
                    r=r.encode("utf8")
                result[key]=r
        return result

    def query_insert (self,struct):
        fields=",".join(["`%s`" % str(v) for v in struct.keys()])
        st=[]
        for k,v in struct.items():
            if v==None or v=='None' or v=='NULL':
                v='NULL'
            else:
                if self.field_list[k] in ('D','t'):
                    v=str(v)
                if self.field_list[k] in ('s','D','t'):
                    v = v.replace("'",'"')
                    v="\'%s\'" % v
            #if type(v)==unicode:
            #    v=v.encode("utf8")
            st.append(v)
        values=",".join(["%s" % v for v in st])
        s="insert into %s (%s) values(%s)" % (self.tablename,fields,values)
        return s

    def query_all_insert(self,data):
        i=0
        struct={}
        for k in self.fieldsorder:
            struct[k]=data[i]
            i=i+1
        return self.query_insert(struct)
    
    def query_update (self,struct):
        st=[]
        for k,v in struct.items():
            if v==None or v=='None' or v=='NULL':
                v='NULL'
            else:
                if self.field_list[k] in ('D','t'):
                    v=str(v)
                if self.field_list[k] in ('s','D','t'):
                    v = v.replace("'",'"')
                    v="\'%s\'" % v
            #if type(v)==unicode:
            #    v=v.encode("utf8")
            st.append("`%s`=%s" % (k,v))
        values=",".join(["%s" % v for v in st])
        s="update %s set %s" % (self.tablename,values)
        return s

    def query_last_id(self):
        return "select last_insert_id()"

    def query_delete(self,ifs):
        return "delete from %s where %s" % (self.tablename,ifs)

    def query_truncate(self):
        return "truncate %s" % (self.tablename)

class db:
    def __init__ (self,dbname,host,user,password):
        self.dbname=dbname
        self.host=host
        self.user=user
        self.password=password

    def open (self,char_set='utf8'):
        try:
            self.db = MySQLdb.connect(host=self.host, user=self.user, passwd=self.password, db=self.dbname, charset=char_set)
            self.cursor = self.db.cursor()
            self.db.autocommit(True)
            return 1
        except:
            return 0 

    def close (self):
        self.cursor.close()
        self.db.close()

    def ping (self):
        try:
            self.run('select 1')
            return True
        except:
            return False
    
    def run (self,query):
        try:
            r=self.cursor.execute(query)
            r=True
        except:
            r=False
            #print "error",query
        return r

    def get (self,query):
        try:
            r=self.run(query)
            data=self.cursor.fetchall()
        except:
            print "error",query
            data=[]
        return data

    def lastid (self):
        r=self.run("select last_insert_id()")
        return r[0][0]


