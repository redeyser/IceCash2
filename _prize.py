#!/usr/bin/python
# -*- coding: utf-8
import dbIceCash,prizeIceCash,sys,random
db = dbIceCash.dbIceCash(dbIceCash.DATABASE, 'localhost', dbIceCash.MYSQL_USER, dbIceCash.MYSQL_PASSWORD)
if db.open():
    pass
else:
    print "DTPWeb Server down. Database not exist"
    sys.exit(1)

db._read_sets()
ps=prizeIceCash.prizeIceCash("1",db.idplace,db.nkassa,db.sets['backoffice_ip'],int(db.sets['prize_port']))
if ps.connect():
    print "Сервер призов доступен\n"
else:
    print "Сервер призов не доступен"
    sys.exit(1)
if not ps.cmd_info():
    print "Сервер деактивирован"
    sys.exit(1)
    
for l in ps.info:
    print l
print "\n"

ncheck=random.randrange(1000)
idtrsc=1
summa=500
if ps.cmd_gen(ncheck,idtrsc,summa):
    print "Результат генерации:",ps.gen
else:
    print "Ошибка генерации приза!!!"
    sys.exit(1)
if  ps.cmd_close():
    print "Транзакция успешно закрыта"
else:
    print "Ошибка закрытия транзакции"
#print "Попытка повторно закрыть транзакцию:"
#print ps.cmd_close()
ps.close()
