# -*- coding: utf-8
import printer

#Epson = printer.Serial("/dev/ttyS0")
Epson = printer.Serial("/dev/ttyUSB0")
#Epson = escpos.Escpos(0x1c8a,0x3012,0,0x81,0x01)
#Epson = printer.Usb(0x1c8a,0x3012,0,in_ep=0x81, out_ep=0x02)
#Epson = printer.Network('172.16.200.8', port=9600)
#s=u"Скорость печати Сегодня большинство прикладных программ работают под Windows XPи Vista, выводящими документ в виде графики. Поэтому проблема скорости печати сводится не столько к скорости протягивания бумаги, сколько к корректной работе драйвера с графикой. Поэтому для TSP650 были разработаны новые драйверы, которые позволяют печатать 19 стандартных чеков с интерфесом LPT (параллельным) и 32 - при использовании USB. Скорость механизма - до 150 мм в секунду (зависит от качества бумаги). Разрешение графики - 203 точки на дюйм.\n"
#s=u"С наступающим новым\n2016 годом!\n\n\n\n"
s=u"test string\n"
#Epson.set(codepage="cp866",realcode=17,bold=True,size="2x",font="c",inverted=False,align="center")
#Epson.set(codepage="cp866",code=17,bold=True,size="2x",font="c",inverted=False,align="center")
#Epson.text(s)
#Epson.barcode("2000000040011","EAN13",255,6,"ABOVE","B")
#Epson.image("unix.png")
#Epson.image("action.png")
#Epson.image("mutant.png")
#Epson.image("mutant2.png")
#for i in range(10):
#Epson.text(s)
#Epson.qr("Привет с большого бодуна")
#Epson.beep()
Epson.set(font="a")
Epson.text(s)
Epson.set(font="b")
Epson.text(s)
Epson.set(font="c")
Epson.text(s)
Epson.cut()
#Epson.cut()
#Epson._get_sensor(1)
#Epson._get_sensor(2)
#Epson._get_sensor(3)
#Epson._get_sensor(4)
#print Epson.is_error()
#Epson.cashdraw(2)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)
#Epson.cashdraw(5)

#Bus 001 Device 004: ID 1c8a:3012  
#Bus 001 Device 003: ID 0424:ec00 Standard Microsystems Corp. SMSC9512/9514 Fast Ethernet Adapter
#Bus 001 Device 002: ID 0424:9514 Standard Microsystems Corp. 
#Bus 001 Device 001: ID 1d6b:0002 Linux Foundation 2.0 root hub
