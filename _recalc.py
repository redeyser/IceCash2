#!/usr/bin/python
# -*- coding: utf-8
import dbIceCash,zIceCash
from clientEgais import *
#Пример скрипта для пересчета зет отчета
db = dbIceCash.dbIceCash(dbIceCash.DATABASE, 'localhost', dbIceCash.MYSQL_USER, dbIceCash.MYSQL_PASSWORD)
if db.open():
    pass
else:
    sys.exit(1)

db._read_sets()
#z=zIceCash.zIceCash(db)
#print z._Z_recalc(1)
egais=EgaisClient(db.sets["egais_ip"],8080,db)
egais._recalc()

