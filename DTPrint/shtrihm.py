#!/usr/bin/python
# -*- coding: utf8 -*-
# frk object v 2.0.007
import kkmdrv
import serial
import time
import Image
import qrcode

const_error=1
const_cmd={'sale':11,'return':13,'X':60,'Z':61,'close_check':55,'cancel_check':56,}

const_code  = u'  Код:'
const_count = u'  Количество'
const_price = u'  Цена'
const_vsego = u'  Всего'
const_itogo = u'Итого'

MAXWIDTH = 48
CMDERR_NO=0
""" Конвертация рисунка в массив битов """
def convert_image(im,img_size):
    """ Parse image and prepare it to a printable format """
    pix_line=""
    for y in range(img_size[1]):
        pix=""
        for x in range(img_size[0]):
            RGB = im.getpixel((x, y))
            im_color = (RGB[0] + RGB[1] + RGB[2])
            if im_color<600:
                b="1"
            else:
                b="0"
            pix += b 
        pix_line +=pix
    return pix_line

def nd_concat(title,value):
    return  title.ljust(kkmdrv.MAXWIDTH-len(value),'.')+value

class frk:

    def __init__(self,port,speed):
        self.MAX_WIDTH=MAXWIDTH
        self.password = kkmdrv.DEFAULT_PASSWORD
        self.admin_password = kkmdrv.DEFAULT_ADM_PASSWORD
        self.port = port
        self.speed = speed

        self.salelines=[]
        self.a_startus=['ready','check','error']
        self.error=0

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, int(self.speed),\
                                 parity=serial.PARITY_NONE,\
                                 stopbits=serial.STOPBITS_ONE,\
                                 timeout=0.7,\
                                 writeTimeout=0.7)
        except:
            return False

        try:
            self.kkm=kkmdrv.KKM(self.ser,password=self.password,wide=self.MAX_WIDTH)
            err=0
            self._status_ready()
            #print "connect frk"
        except:
            err=const_error
            self._status_error()
            #print "not connect frk"
        return True

    def disconnect(self):
        try:
            self.ser.close()
            return 0
        except:
            return 1

    def _status_ready(self):
        self.status='ready'
        self.error=0

    def _status_check(self,t):
        self.status='check'
        self.check_type=t

    def _status_error(self):
        self.status='error'
        self.error=1

    def _iserror(self):
        if self.status=='error':
            return True
        else:
            return False

    def _beep(self):
        try:
            err=self.kkm._beep()
        except:
            err=const_error
            self._status_error()
        return err

    def setPort(self,port,speed,timeout):
        try:
            err=self.kkm.setPort(port,speed,timeout)
        except:
            err=const_error
            self._status_error()
        return err

    def getPort(self,port):
        try:
            err=self.kkm.getPort(port)
            self.PortSets=self.kkm.PortSets
        except:
            err=const_error
            self._status_error()
        return err

    def tableStruct(self,number):
        try:
            err=self.kkm.getTableStruct(number)
            self.TableStruct=self.kkm.TableStruct
            self.TableStruct[2]=self.TableStruct[2][0:self.TableStruct[2].find("\x00")]
            self.TableStruct[2]=self.TableStruct[2].decode('cp1251').encode('utf8')

        except:
            err=const_error
            self._status_error()

        return err

    def fieldStruct(self,table,row,field):
        try:
            err=self.kkm.getTableValue(table,row,field)
            self.FieldStruct=self.kkm.FieldStruct
            self.FieldStruct[4]=self.FieldStruct[4][0:self.FieldStruct[4].find("\x00")]
            self.FieldStruct[4]=self.FieldStruct[4].decode('cp1251').encode('utf8')
        except:
            err=const_error
            self._status_error()

        return err

    def setTableValue(self,table,row,field,value):
        try:
            value=value.encode('utf8')
            err=self.kkm.setTableValue(table,row,field,value)
        except:
            err=const_error
            self._status_error()

        return err

    def prn_devstatus(self):
        try:
            self.DEVICE=self.kkm.statusRequest()
            err=0
        except:
            err=const_error
            self._status_error()
        return err

    def _opencheck(self,t):
        try:
            err=self.kkm._opencheck(t)
            if not err:
                self._status_check(t)
            else:
                self._cancelcheck()
        except:
            self.continuePrint()
            self.continuePrint()
            self._cancelcheck()
            err=const_error
            self._status_error()
        return err

    def _opensmena(self):
        try:
            err=self.kkm._opensmena()
            if not err:
                self._status_check(t)
            else:
                self._cancelcheck()
        except:
            err=const_error
            self._status_error()
        return err

    def _discount(self,lastposition=0,issum=1,isgrow=0,value="0"):
        try:
            err=self.kkm._discount(lastposition,issum,isgrow,value)
            if not err:
                self._status_check(0)
        except:
            err=const_error
            self._status_error()
        return err

    def _outcash(self,summa):
        try:
            err=self.kkm._outcash(summa)
            if not err:
                self._status_check(0)
        except:
            err=const_error
            self._status_error()
        return err

    def _incash(self,summa):
        try:
            err=self.kkm._incash(summa)
            if not err:
                self._status_check(0)
        except:
            err=const_error
            self._status_error()
        return err

    def _register(self,price,count,section):
        try:
            err=self.kkm._register(price,count,section)
            if not err:
                self._status_check(0)
        except:
            err=const_error
            self._status_error()
        return err

    def _registerpos(self,title,price,count,section):
        try:
            err=self.kkm._register(price,count,section,title)
            if not err:
                self._status_check(0)
        except:
            err=const_error
            self._status_error()
        return err

    def _return(self,price,count):
        try:
            err=self.kkm._return(price,count,"1")
            if not err:
                self._status_check(1)
        except:
            err=const_error
            self._status_error()
        return err

    def _returnpos(self,title,price,count,section):
        try:
            err=self.kkm._return(price,count,section,title)
            if not err:
                self._status_check(0)
        except:
            err=const_error
            self._status_error()
        return err

    def _preitog(self):
        try:
            err=self.kkm._preitog()
        except:
            err=const_error
            self._status_error()
        return err
    
    def _closecheck(self,summa,summa2,skid=0):
        try:
            err=self.kkm._closecheck(summa,summa2,discount=skid,text=u"")
            if not err:
                self._status_ready()
            else:
                self._cancelcheck()
        except:
            self._cancelcheck()
            err=const_error
            self._status_error()
        return err

    def _cancelcheck(self):
        try:
            err=self.kkm._cancelcheck()
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _reportX(self):
        try:
            err=self.kkm._reportX(self.admin_password)
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _reportZ(self):
        try:
            err=self.kkm._reportZ(self.admin_password)
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _cut(self,_type):
        try:
            err=self.kkm.cutCheck(_type)
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def continuePrint(self):
        try:
            err=self.kkm.continuePrint()
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def repeatDoc(self):
        try:
            err=self.kkm.repeatDoc()
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def prn_setcurdate(self):
        t=time.gmtime()
        try:
            err=self.kkm.setDate(self.admin_password,t.tm_mday,t.tm_mon,t.tm_year)
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def prn_acceptdate(self):
        t=time.localtime()
        try:
            err=self.kkm.acceptSetDate(self.admin_password,t.tm_mday,t.tm_mon,t.tm_year)
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def prn_setcurtime(self):
        t=time.localtime()
        try:
            err=self.kkm.setTime(self.admin_password,t.tm_hour,t.tm_min,t.tm_sec)
            if not err:
                self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _printsh(self):
        try:
            self.kkm._printsh()
            self._status_ready()
            err=0
        except:
            err=const_error
            self._status_error()
        return err

    def _print(self,t=u""):
        try:
            self.kkm._print(text=t)
            self._status_ready()
            err=0
        except:
            print t
            err=const_error
            self._status_error()
        return err

    def _printf(self,t,f):
        try:
            self.kkm._printf(t,f)
            self._status_ready()
            err=0
        except:
            err=const_error
            self._status_error()
        return err

    """ Линия символов """
    def prn_line(self,ch):
        self._print(ch*self.MAX_WIDTH)

    """ Комплексный метод печати. Текст с переносом на следующую строку, признаком крупного текста, настройками стиля"""
    def prn_lines(self,text="",width=0,font=1,bright=0,big=0,height=0,invert=0,align='left'):
        if text=="":
            return
        if font==0:
            font=1
        if big==1 or height==1:
            big=1
            font=2
        if width==0:
            width=self.MAX_WIDTH
        atext=text.split("\n")
        #print "prn_lines",text,font
        for s in atext:
            while len(s)>0:
                if len(s)>width:
                    t=s[:width]
                    s=s[width:]
                else:
                    t=s
                    s=""
                if align=='centers':
                    if big:
                        m=self.MAX_WIDTH/2
                    else:
                        m=self.MAX_WIDTH
                    t=t.center(m," ")
                self._printf(t,font)

    """ Печать в стиле Цена......100.00 """
    def prn_sale_style(self,text="",val="",ch=" "):
        lt=len(text)
        lv=len(val)
        ld=self.MAX_WIDTH-lv
        stext=text.ljust(ld,ch)
        s=stext+val
        self._print(s)

    """ Печать в стиле Цена X Количество = Стоимость, второй строчкой бонус и дисконт """
    def prn_sale_short(self,fiscal,title,_type,section,realcena,p1,p2,p3,ch1,b,d,ch2,ofd):
        if fiscal!=1:
            text="["+str(section)+"] "+p2+" X "+p1
            val="="+p3
            lt=len(text)
            lv=len(val)
            ld=self.MAX_WIDTH-lv
            stext=text.ljust(ld,ch1)
            s=stext+val
            self.prn_lines(s,font=0)
        else:
            if ofd:
                if _type=='sale':
                    self._registerpos(title,realcena,p2,section=section)
                else:
                    self._returnpos(title,realcena,p2,section=section)
            else:
                if _type=='sale':
                    self._register(p1,p2,section)
                else:
                    self._return(p1,p2)
            if self.error != CMDERR_NO:
                return False
        if b!="" and  b!="0.00":
            tb=u"бонус: %s " % b
        else:
            tb=""
        if d!="" and d!="0.00":
            td=u"скидка: %s" % d
        else:
            td=""
        text="%s%s" % (tb,td)
        self.prn_lines(text,bright=10,font=3)
        self.prn_line(ch2)

    """ Печать Итога """
    def prn_sale_itog(self,vsego="",discount="",itogo="",nal="",bnal="",sdacha="",ch=" "):
        self.prn_sale_style(text=u"ВСЕГО",val="="+vsego,ch=ch)
        self.prn_sale_style(text=u" СКИДКА",val="="+discount,ch=ch)
        val="="+itogo
        text=u'ИТОГ'
        lt=len(text)
        lv=len(val)
        ld=self.MAX_WIDTH/2-lv
        stext=text.ljust(ld,ch)
        s=stext+val
        self.prn_lines(s,height=1,font=2,big=True)
        self.prn_sale_style(text=u"НАЛИЧНЫМИ",val="="+nal,ch=ch)
        self.prn_sale_style(text=u"БЕЗНАЛИЧНЫМИ",val="="+bnal,ch=ch)
        self.prn_sale_style(text=u"СДАЧА",val="="+sdacha,ch=ch)

    def prn_sale_head(self,ncheck,dt,tm):
        self.prn_sale_style(text="#"+ncheck,val=dt+" "+tm,ch=" ")

    def loadGraphLines(self,data):
        try:
            err=self.kkm.loadGraphLines(data)
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def loadGraphFile(self,nfile):
        try:
            err=self.kkm.loadGraphFile(nfile)
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def loadGraph(self,line,sbits):
        try:
            err=self.kkm.loadGraph(line,sbits)
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def printGraph(self,l1,l2):
        try:
            err=self.kkm.printGraph(l1,l2)
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _printcode(self,text):
        try:
            err=self.kkm._printcode(text)
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _openbox(self):
        try:
            err=self.kkm.openbox()
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _roll(self,n):
        try:
            err=self.kkm.roll(n)
            self._status_ready()
        except:
            err=const_error
            self._status_error()
        return err

    def _renull(self):
        try:
            self.kkm.renull()
            self._status_ready()
            err=0
        except:
            err=const_error
            self._status_error()
        return err

    def print_image(self,im):
        if im.size[0] > self.MAX_PIXEL_WIDTH:
            return False
        if im.size[1] > kkmdrv.MAX_PIXELS_HEIGHT:
            return False

        img_size=[0,0]
        img_size[0] = (im.size[0]//8)*8
        img_size[1] = im.size[1]

        line = convert_image(im,img_size)

        img_bytes_width=img_size[0]/8
        data=""
        for y in range(img_size[1]):
            buffer = ""
            for x in range(img_bytes_width):
                s = list(line[(y*img_size[0]+x*8):(y*img_size[0]+x*8+8)])
                s.reverse()
                s = "".join(s)
                buffer += "%02X" % int(s,2)
            dataline=buffer.decode("hex")
            dataline=dataline.ljust(40,chr(0x0))[:40]
            data+=dataline
        self.loadGraphLines(data)
        err=self.printGraph(1,y)
        return err

    def prn_image(self,path_img=""):
        """print image file """
        im_open = Image.open(path_img)
        im = im_open.convert("RGB")
        return self.print_image(im)

    def prn_qr(self, text, *args, **kwargs):
        """ Print QR Code for the provided string """
        qr_args = dict(
            version=4,
            box_size=4,
            border=1,
            error_correction=qrcode.ERROR_CORRECT_M
        )

        qr_args.update(kwargs)
        qr_code = qrcode.QRCode(**qr_args)

        qr_code.add_data(text)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image()
        im = qr_img._img.convert("RGB")
        print "qrcode"
        return self.print_image(im)

    def writesets_text(self,text12,text13,text14):
        try:
            self.kkm.setTableValue(4,12,1,text12.center(30))
            self.kkm.setTableValue(4,13,1,text13.center(30))
            self.kkm.setTableValue(4,14,1,text14.center(30))
            err=0
        except:
            err=const_error
            self._status_error()
        return err

    def writesets(self,autonull,openbox,autocut):
        try:
            self.kkm.setTableValue(1,1,2,int(autonull))
            self.kkm.setTableValue(1,1,6,int(openbox))
            self.kkm.setTableValue(1,1,7,int(autocut))
            self._status_ready()
            err=0
        except:
            err=const_error
            self._status_error()
        return err

    def nd_set_tables(self,title1,title2):
        t1=title1.center(24).encode('utf8')
        t2=title2.center(24).encode('utf8')
        self.kkm.setTableValue(1,1,17,1)
        self.kkm.setTableValue(4,13,1,t1)
        self.kkm.setTableValue(4,14,1,t2)


#Пример. Потото закоментировать или удалить
#Подключаемся
#D=frk('/dev/ttyS2',115200)
#D=frk('/dev/ttyUSB0',115200)
#D.connect()
#D._opensmena()
#D._cancelcheck()
#print D._opencheck(0)
#print D._registerpos(u"KUINA BLA BLA BLA","10.0","1.0","1")
#print D._closecheck("10.0","0.0")
#print D.kkm.shortStatusRequest()
#print D.kkm.statusRequest()
#Можно отменить последний чек если были ошибки
#Это нужно слать один раз в самом начале. Или вообще один раз при настройке.
#D.nd_set_tables(u'ООО "Олимпик"',u'пр. Косыгина д. 26')
#Открываем чек
#0-продажа 2-возврат
#D.nd_openCheck(0)
#Печатаем продажи
#D.nd_Sale(u"1.22633 Для кастриров.котов с чувств.кожей:\n1-7 лет (Neutered Skin Yang Male) 744004",2167,2,250)
#D.nd_Sale(u"1.22633 Для кастриров.котов с чувств.кожей:\n1-7 лет (Neutered Skin Yang Male) 744004",2167,4,250)
#D.nd_Storno(u"1.22633 Для кастриров.котов с чувств.кожей:\n1-7 лет (Neutered Skin Yang Male) 744004",2167,4,250)

#Закрываем чек
#D.nd_closeCheck(1000,500,0)
#Отключаемся
#D._printsh()
#D._printcode(text="2303397000003")
#D._print(t=u"sjdhfksfhksdf")
#D._roll(10)
#D._cut(1)
#D.loadGraphLines(chr(0b11000111)*40*200)
#D.print_imagefile("z.png")
#D.print_imagefile("icecash.png")
#D.print_imagefile("mutant.png")
#D.print_qrcode("http://check.egais.ru?id=47fa33bf-4958-45cb-a248-5aa0479ae8ae&dt=1606161524&cn=020000606823")
#D.disconnect()


