#!/usr/bin/python
# -*- coding: utf8 -*-
# version 1.0.004

import time
import serial
import socket
import string,time
import Image
import qrcode
import time
import sys 
from struct import pack, unpack

""" Драйвер принтеров FPrint
    Романенко Руслан Андреевич
    Кемерово (2017)
    ----------------------------
    v 1.0.005 2017-03-19
    author : Redeyser
    mail   : redeyser@gmail.com
    Lic    : GPL
    ----------------------------
    -   prn_sale_short:
        новый параметр - realcena. Цена отправляемая в ФРК
    -   для печати ОФД QR-кода : 
        prn_tabset(value="1",tabval="printofd",incrow=0,nvalues=1)
    -   Ошибка в self.error может содержать 
        0 - нет ошибок
        1 - ошибка в процессе обмена, 
        2 - ошибка длинных ответа
        И далее по руководству драйвера ошибки фискальника.

    2016-04-10
        Подвисает подсчет суммы, убрал из dev_status
"""

""" Функции конвертации """
""" Массив байтовых чисел в строку данных """
def bufStr(*b):
    result = []
    for x in b: result.append(chr(x))
    return string.join(result,'')

""" Строка данных в HEX виде """
def hexStr(s):
    result = []
    for c in s: result.append(hex(ord(c)))
    return string.join(result,' ')

""" Обычный текст в крупный """
def txt2bigtxt(s):
    return "\t"+"\t".join(list(s))

""" Текст из кодировки FPRINT в обычный с префиксом крупного текста """
def fpcode2txt(s):
    if s.find("\xfe")!=-1:
        s=s.replace("\xfe",chr(94))
    r=""
    l=len(FPRINT_CHARSET)
    for c in s:
        for i in range(l):
            (n,c1,c2) = FPRINT_CHARSET[i]
            if (i==l-1) or ( ord(c)>=n and ord(c)<FPRINT_CHARSET[i+1][0] ):
                z=c1-n
                c=chr(ord(c)+z)
                break
        r+=c
    return (r.decode("cp866"))

""" На самом деле это просто перевод в кодировку cp866 и замена ^ на /t """
def data2fpcode(s):
    return s.replace("^","\t").encode("cp866")

""" Дата в BCD"""
def date2BCD(d):
    return d.replace(".","")

""" BCD в виде даты"""
def BCD2date(d):
    return d[:2]+'.'+d[2:4]+'.'+d[4:6]

""" Вставить десятичную точку в строку BCD формата"""
def BCD2sval(s,n):
    r=s[:-n].lstrip('0')+"."+s[-n:]
    if r[0]=='.':
        r="0"+r
    return r

""" Убрать десятичную точку из строки BCD формата"""
def sval2BCD(s,n):
    return s.replace(".","").rjust(n,'0')

""" Строка данных в BCD с разделителем """
def data2sval(d,n):
    s=data2BCD(d)
    return BCD2sval(s,n)

""" Из BCD с разделителем в строку данных """
def sval2data(s,n):
    BCD=s.replace(".","").rjust(n,'0')
    return BCD2data(BCD,n)

""" Целое число в строку данных длинной n """
def int2data(X,r):
    result=[]
    while X!=0:
        n=X//256
        m=X%256
        if n!=0:
            result.append(chr(m))
        else:
            result.append(chr(X))
        X=n
    result.reverse()
    return string.join(result,'').rjust(r,NULL)

""" Строка в формат BCD """
def data2BCD(data,n=0):
    r=""
    for i in range(len(data)):
        r += "%02X" % ord(data[i])
    if n==0:
        return r
    else:
        return r[-n:]

""" Из BCD в строку данных """
def BCD2data(BCD,m=0):
    if m == 0:
        n=len(BCD)/2
        if n<1:
            n=1
    else:
        n=m
    return int2data(int(BCD,16),n)

""" Строка данных в целое число """
def data2int(d,n,m):
    result=0
    s=0
    for x in range(m):
        c=ord(d[n+x])
        result=result+c*256**s
        s=s+1
    return result

""" Строка данных в массив целых чисел """
def data2ints(data,sizes):
    n=0
    result=[]
    for size in sizes:
        d=data2int(data,n,size)
        result.append(d)
        n=n+size
    return result
    
""" Строка данных в массив строк """
def data2bufs(data,sizes):
    n=0
    result=[]
    for size in sizes:
        d=data[n:n+size]
        result.append(d)
        n=n+size
    return result

""" Строка данных в массив BCD значений """
def data2bufsBCD(data,sizes):
    res = data2bufs(data,sizes)
    result=[]
    n=0
    for d in res:
        result.append(data2BCD(d))
        n+=1
    return result

""" Байтовое число в массив логических значений """
def byte2array(b):
        """Convert byte into array"""
        result = []
        for i in range(0,8):
                if b == b >> 1 <<1:
                        result.append(False)
                else:
                        result.append(True)
                b = b >>1
        return result

""" Байт разделить на два полубайта """
def byte2tet(b):
    B=bin(b)[2:].rjust(8,"0")
    return [int(B[0:4],2),int(B[4:8],2)]

""" Конвертация рисунка в массив битов """
def convert_image(im,img_size):
    """ Parse image and prepare it to a printable format """
    pix_line=""
    for y in range(img_size[1]):
        pix=""
        for x in range(img_size[0]):
            RGB = im.getpixel((x, y))
            im_color = (RGB[0] + RGB[1] + RGB[2])
            if im_color<200:
                b="1"
            else:
                b="0"
            pix += b 
        pix_line +=pix
    return pix_line

def LRC(buff):
    """Подсчет CRC"""
    result = 0
    for c in buff:
        result = result ^ ord(c)
    return chr(result)

""" CONSTANTS """
FPRINT_CHARSET = [
    [ 0x00, ord(u"А".encode("cp866")),ord(u"Я".encode("cp866")) ],\
    [ 0x20, ord(u" ".encode("cp866")),ord(u"/".encode("cp866")) ],\
    [ 0x30, ord(u"0".encode("cp866")),ord(u"~".encode("cp866")) ],\
    [ 0x80, ord(u"а".encode("cp866")),ord(u"п".encode("cp866")) ],\
    [ 0x90, ord(u"р".encode("cp866")),ord(u"ё".encode("cp866")) ],\
]

CMDERR_NO = 0
CMDERR_PT = 1
CMDERR_LN = 2

NULL= chr(0x00)
ENQ = chr(0x05)
STX = chr(0x02)
ACK = chr(0x06)
NAK = chr(0x15)
ETX = chr(0x03)
EOT = chr(0x04)
DLE = chr(0x10)
ANS = chr(0x55)

DEFAULT_PORT="/dev/ttyS0"
DEFAULT_SPEED=115200
DEFAULT_PASSWORD = bufStr(0x00,0x00)
DEFAULT_PASSWORD_ADMIN = bufStr(0x00,0x30)
DEFAULT_MAX_WIDTH = 36
DEFAULT_MAX_PIXELS_WIDTH  = 384
DEFAULT_MAX_PIXELS_HEIGHT = 4096

T1 = 0.5
T5 = 10
T8 = 1
TM = 40
tmX= 4
tmZ= 8
tmO= 1
tmC= 1

SPEED = { 
    "1200"  : "01",\
    "2400"  : "02",\
    "4800"  : "03",\
    "9600"  : "04",\
    "14400" : "05",\
    "38400" : "06",\
    "57600" : "07",\
    "115200": "08",\
}

TABLE_VALUES = {
    'autocut'   : [2,1 ,24,'BCD'],\
    'autobox'   : [2,1 ,20,'BCD'],\
    'autonull'  : [2,1 ,28,'BCD'],\
    'font'      : [2,1 ,32,'BCD'],\
    'bright'    : [2,1 ,19,'BCD'],\
    'roll'      : [2,1 ,36,'BCD'],\
    'summertm'  : [2,1 ,52,'BCD'],\
    'passkassir': [3,1 ,1 ,'BCD'],\
    'passadmin' : [3,30,1 ,'BCD'],\
    'textlines' : [6,1 ,1 ,'CHR'],\
    'sections'  : [7,1 ,1 ,'CHR'],\
    'typedev'   : [9,1 ,1 ,'BCD'],\
    'speed'     : [9,1 ,2 ,'BCD'],\
    'printofd'  : [2,1 ,14,'BCD'],\
    }

TYPE_CHECK = {\
    'sale'      : chr(0x1),\
    'retsale'   : chr(0x2),\
    'cancel'    : chr(0x3),\
    'buy'       : chr(0x4),\
    'retbuy'    : chr(0x5),\
    }

REGISTERS = {\
    'sum'       : [ chr(0x0a),NULL,NULL, [7]           ],\
    'vir'       : [ chr(0x0b),NULL,NULL, [1,6]         ],\
    'datetime'  : [ chr(0x11),NULL,NULL, [3,3]         ],\
    'ncheck'    : [ chr(0x13),NULL,NULL, [1,1,2,4]     ],\
    'deviceid'  : [ chr(0x16),NULL,NULL, [4]           ],\
    'width'     : [ chr(0x18),NULL,NULL, [1,2,1,2,1,2] ],\
    'inn'       : [ chr(0x1b),NULL,NULL, [6,5,2,3]     ],\
    'eklz'      : [ chr(0x1c),NULL,NULL, [4,3,2]       ],\
    }

FLAGS_STATUS = {\
    'f_fiskal'      : [0,'Фискализирован'],\
    'f_opensm'      : [1,'Смена открыта'],\
    'f_closebox'    : [2,'Ящик открыт'],\
    'f_ispaper'     : [3,'Бумага есть'],\
    'f_opencap'     : [5,'Крышка открыта'],\
    'f_easypower'   : [7,'Слабое напряжение батарейки'],\
    }

MODES = { \
    'select'      : [0x0,"Выбор"],\
    'reg'         : [0x1,"Регистрация"],\
    'otx'         : [0x2,"Отчет без гашения"],\
    'otz'         : [0x3,"Отчет с гашением"],\
    'prog'        : [0x4,"Программирование"],\
    'fp'          : [0x5,"Доступ к ФП"],\
    'eklz'        : [0x6,"Доступ к ЭКЛЗ"],\
    }

COMMANDS = { \
    'print'       : [0x4c,T5,"Печать строки"],\
    'printf'      : [0x87,T5,"Печать поля"],\
    'printim'     : [0x8e,TM,"Печать картинки"],\
    'printsh'     : [0x6c,T5,"Печать клише"],\
    'printcode'   : [0xc1,T5,"Печать штрихкода"],\
    'retrycheck'  : [0x95,T5,"Повторная печать последнего докумена"],\
    'printdemo'   : [0x82,T5,"Демонстрационная печать"],\

    'beep'        : [0x47,0 ,"Гудок"],\
    'sound'       : [0x88,TM,"Звуковой сигнал"],\
    'openbox_im'  : [0x85,T5,"Импульсное открытие денежного ящика"],\
    'openbox'     : [0x80,T5,"Открыть денежный ящик"],\
    'cut'         : [0x75,T5,"Отрезка"],\

    'setmode'     : [0x56,T5,"Вход в режим"],\
    'exitmode'    : [0x48,T5,"Выход из текущего режима"],\
    'status'      : [0x3F,TM,"Запрос состояния ККТ"],\
    'getsum'      : [0x4D,T5,"Запрос суммы наличности"],\
    'getX'        : [0x58,T5,"Запрос последнего сменного итога продаж"],\
    'codestatus'  : [0x45,T5,"Запрос кода состояния ККТ"],\
    'typedev'     : [0xA5,T5,"Получить тип устройства"],\
    'readreg'     : [0x91,T5,"Чтение регистров"],\

    'setdate'     : [0x64,T5,"Программирование даты"],\
    'settime'     : [0x4B,T5,"Программирование времени"],\
    'renull'      : [0x6B,TM,"Технологическое обнуление"],\
    'defaulttabs' : [0x71,TM,"Инициализация таблиц начальными значениями"],\
    'settabvalue' : [0x50,T5,"Установка значения в таблице"],\
    'gettabvalue' : [0x46,T5,"Чтение значения в таблице"],\

    'opensmena'   : [0x9A,T5,"Открыть смену"],\
    'opencheck'   : [0x92,T5,"Открыть чек"],\
    'cancelcheck' : [0x59,T5,"Аннулировать открытый чек"],\
    'incash'      : [0x49,T5,"Внесение денег"],\
    'outcash'     : [0x4F,T5,"Выплата денег"],\
    'register'    : [0x52,T5,"Регистрация"],\
    'registerpos' : [0xE6,T5,"Регистрация Позиции"],\
    'return'      : [0x57,T5,"Возврат"],\
    'returnpos'   : [0xE7,T5,"Сторнирование Регистрации Позиции"],\
    'discount'    : [0x43,T5,"Начисление скидки/надбавки"],\
    'closecheck'  : [0x4a,T5,"Закрытие чека"],\
    'reportX'     : [0x67,TM,"Начало снятия отчета без гашения"],\
    'reportZ'     : [0x5A,TM,"Снятие суточного отчета с гашением"],\
}

class KKM_FPRINT:

    def __init__(self,port=DEFAULT_PORT,speed=DEFAULT_SPEED,password=DEFAULT_PASSWORD,admpassword=DEFAULT_PASSWORD_ADMIN,echo=False,ip=""):
        """ DEFAULT SETS """
        if ip!='':
            self._read=self._read_socket
            self._write=self._write_socket
            self.isnet=True
        else:
            self._read=self._read_serial
            self._write=self._write_serial
            self.isnet=False
        self.tabvalues={}
        self.DEVICE={ 'dev_wchar':DEFAULT_MAX_WIDTH,'dev_wpix':DEFAULT_MAX_PIXELS_WIDTH }
        self.ncheck=0
        self.echo=echo
        self.error=CMDERR_NO
        self.sflags={}
        self.csflags={}
        self.device={}
        self.status={}
        self.port=port
        self.ip=ip
        self.speed=speed
        self.answer=""
        self.password=password
        self.admpassword=admpassword
        self.MAX_PIXELS_HEIGHT=DEFAULT_MAX_PIXELS_HEIGHT
        print "%s:%s" % (ip,port)

    def disconnect(self):
        try:
            self.conn.close()
            return True
        except:
            return False

    def connect(self):
        try:
            if not self.isnet:
            #print "connect to %s %d" % (self.port, self.speed)
                self.conn = serial.Serial(self.port, self.speed,\
                                     parity=serial.PARITY_NONE,\
                                     stopbits=serial.STOPBITS_ONE,\
                                     timeout=0.7,\
                                     writeTimeout=0.7)
                """ self._exitmode()
                    self.prn_devstatus()
                """
            else:
                self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.conn.connect((self.ip, self.port))
            self.MAX_WIDTH=self.DEVICE['dev_wchar']
            self.MAX_PIXELS_WIDTH=self.DEVICE['dev_wpix'] 
            self.debug("connected")
            return True
        except:
            return False

    """ Внутренние низкоуровневые методы, реализующие общие принципы протокола обмена данными
        =====================================================================================
    """
    def debug(self,val):
        if self.echo:
            print val

    def _ecranETX(self,data):
        result=[]
        for b in data:
            if (b==ETX)or(b==DLE):
                result.append(DLE)
            result.append(b)
        return string.join(result,"")

    def _deecran_ETX_DLE(self,data):
        result=[]
        b_old=chr(0x00)
        for b in data:
            if (b_old==DLE):
                result[result.__len__()-1] = b
                b_old=chr(0x00)
            else:
                result.append(b)
                b_old=b
        return string.join(result,"")

    def _read_serial(self,n):
        return self.conn.read (n)

    def _write_serial(self,b):
        return self.conn.write (b)

    def _read_socket(self,n):
        return self.conn.recv(n)

    def _write_socket(self,b):
        #print "send socket %s" % b
        r= self.conn.send (b)
        #print r
        return r

    def _read_byte(self,b,max_timeout=T1):
        _continue = True
        timeout=0
        while _continue:
            try:
                self.answerbyte = self._read (1)
            except:
                self.answerbyte=""
            if (timeout>max_timeout)or(len(self.answerbyte) > 0):
                break
            else:
                time.sleep(T1)
                timeout=timeout+T1
                print "timequery: %d" % timeout
        self.debug(hexStr(self.answerbyte))
        if (b==self.answerbyte):
            return True
        else:
            print "error len="+str(len(self.answerbyte))+",b="+hexStr(b)
            return False

    def _read_bytes2ETX(self):
        _continue=True
        b_old=chr(0x0)
        result=[]
        while (_continue):
            b=self._read(1)
            if (b==ETX)and(b_old!=DLE):
                break
            result.append(b)
            b_old=b
        return string.join(result,"")

    def _write_byte(self,b):
        self._write(b)
        return True

    def _send_command(self,command,data):
        self.error=CMDERR_NO
        self.debug("_start_query")
        cmd = chr(COMMANDS[command][0])
        t5  = COMMANDS[command][1]
        self.answer=""

        if not self.isnet:
            self.conn.flush()

        ret=0
        """ Опрашиваем фискальник на готовность принять запрос """
        while ret<3:
            ret+=1
            self._write_byte(ENQ)
            if not self._read_byte(ACK):
                self._send_werror()
                self.error=CMDERR_PT
                print "_retry_ready"
            else:
                self.error=CMDERR_NO
                break

        if self.error==CMDERR_PT:
            print "_error_ready"
            return False

        edata = self._ecranETX(self.password+cmd+data)
        CRC = LRC(edata+ETX)

        self._write(STX+edata+ETX+CRC)
        self.debug(">> "+hexStr(STX+edata+ETX+CRC))
        if not self._read_byte(ACK):
            self.error=CMDERR_PT
            return False

        self._write_byte(EOT)
        if t5==0:
            return True
        self.debug("_end_query")

        """ Обрабатываем зависание фискальника """
        if not self._read_byte(ENQ,t5):
            self.error=CMDERR_PT
            self._send_werror()
            print "_error_eot"
            return False

        self._write_byte(ACK)

        """ Пропускаем все повторения об ответе ККМ """
        self.answerbyte=ENQ
        while self.answerbyte==ENQ:
            self.debug("_read_STX")
            self._read_byte(STX)

        if self.answerbyte!=STX:
            self.error=CMDERR_PT
            print "_error_STX"
            return False

        data=self._read_bytes2ETX()

        self.debug("_full_answer="+hexStr(data))
        crc=self._read(1)
        CRC=LRC(data+ETX)

        self._write_byte(ACK)
        if not self._read_byte(EOT):
            print "_error_EOT"
            self.error=CMDERR_PT
            return False

        if crc!=CRC:
            print "_error_CRC"
            self.error=CMDERR_PT
            self.answer=""
            return False
        else:
            self.answer=self._deecran_ETX_DLE(data)
            self.debug("_answer_data="+hexStr(self.answer))

        self.debug("_end_answer")

        if len(self.answer) > 0 and self.answer[0]==ANS and command!='codestatus':
            if self.answer[1]!=NULL:
                self.error=ord(self.answer[1])
                print "error:%s" % (hex(self.error))
                return False

        self.error=CMDERR_NO
        return True


    def _send_werror(self):
        print "_send_werror"
        for x in range(5):
            self._write_byte(ENQ)
            time.sleep(T1)
        self._write_byte(EOT)
        #self._read_byte(NAK)

    def _iserror(self,alen=0):
        if len(self.answer)<alen:
            if self.error==CMDERR_NO:
                self.error=CMDERR_LN
            return True
        else:
            if self.error!=CMDERR_NO:
                return True
            else:
                return False

    """ ЗВУК ПЕЧАТЬ ОТРЕЗКА ДЕНЕЖНЫЙ_ЯЩИК
        =====================================================================================
    """

    def _beep(self):
        self._send_command("beep","")

    def _sound(self,hz,tm):
        d=int(65536-(921600/hz))
        d=int2data(d,2)
        self.debug(hexStr(d))
        data=d+chr(tm)
        self._send_command("sound",data)

    def _printim(self,retry=32,margin=32,data="\xff"*48):
        _printer=chr(0x01)
        _retry=int2data(retry,2)
        _margin=int2data(margin,2)

        self._send_command("printim",_printer+_retry+_margin+data)

    def _printcode(self,t=0,align=2,width=3,text=""):
        print "driver:printcode"
        """ 
            type [0,1,2] qr pdf ean13
            align =  [1,2,3]
            width =  koef*
        """
        _type=chr(t)
        _align=chr(align)
        _width=chr(width)
        _version=NULL+NULL
        if type==1:
            _opt=chr(0x01)+chr(0x01)
        else:
            _opt=NULL+NULL
        _korr=NULL
        _count=NULL+NULL
        _prop=NULL*4
        
        data=_type+_align+_width+_version+_opt+_korr+_count+_prop+text.encode('utf8')
        self._send_command("printcode",data)

    def _printf(self,text="",font=0,height=0,bright=0,style=[0,0,0]):
        """ font =  [0,1..4]
            hight=  [0,1,3]
            bright= [0,1..15]
            style [bold,_,invers]
        """
        _flags=NULL
        _printer=chr(0x01)
        _font=chr(font)         
        _height=chr(height)
        _line=NULL
        _bright=chr(bright)
        _mode1=chr(0x01)
        _mode2=chr(0x01)
        _style=str(int(str(style[0])+str(style[1])+str(style[2]),2))

        data=_flags+_printer+_font+_height+_line+_bright+_mode1+_mode2+_style+NULL+NULL+text.encode('cp866')
        self._send_command("printf",data)

    def _print(self,data):
        self._send_command("print",data.encode('cp866'))

    def _printdemo(self):
        self._exitmode()
        if not self._setmode("select",self.admpassword):
            return
        self._send_command("printdemo",chr(0x1)+NULL*2)

    def _printsh(self):
        self._send_command("printsh","")

    def _retrycheck(self):
        self._send_command("retrycheck","")

    def _cut(self,full):
        if full:
            data=chr(0)
        else:
            data=chr(1)
        self._send_command("cut",data)

    def _openbox_im(self):
        data=int2data(20,2)+int2data(2,2)
        self._send_command("openbox_im",data)

    def _openbox(self):
        self._send_command("openbox","")

    """ Переключение между режимами
        =====================================================================================
    """

    def _setmode(self,mode,pas):
        data=chr(MODES[mode][0])
        pas=NULL+NULL+pas
        self._send_command("setmode",data+pas)
        return not self._iserror()
    
    def _exitmode(self):
        """ Сохраняем результат предыдущей команды """
        er=self.error
        self._send_command("exitmode","")
        self.error=er

    """ Получение данных
        =====================================================================================
    """

    def _codestatus(self):
        self._send_command("codestatus","")
        if self._iserror():
            return
        (b55,mode,f) = data2ints(self.answer,[1,1,1])
        f=byte2array(f)
        self.csflags={\
            'fc_notpaper'       : f[0],\
            'fc_disconnect'     : f[1],\
            'fc_braked'         : f[2],\
            'fc_nocut'          : f[3],\
            'fc_hot'            : f[4]\
            }

    def _getsum(self):
        self._send_command("getsum","")
        if self._iserror():
            return
        return data2sval(self.answer[1:],2)

    def prn_getcheck(self):
        ncheck=self._readreg('ncheck')
        self.ncheck=int(ncheck[2])
        if self._iserror():
            self.ncheck=0
        return self.ncheck

    def _getX(self):
        self._send_command("getX","")
        if self._iserror():
            return
        return data2sval(self.answer[2:],2)

    def _status(self):
        self._send_command("status","")

        if self._iserror():
            return False

        (   answer,\
            kassir,zal,\
            date,time,\
            flags,\
            id,\
            model,\
            version,mode,\
            check,smena,\
            stcheck,sumcheck,floatdec,\
            port ) =  data2bufs(self.answer,[1,1,1,3,3,1,4,1,2,1,2,2,1,5,1,1])

        self.status = {\
            'kassir'   : data2BCD(kassir),\
            'zal'      : ord(zal),\
            'date'     : data2BCD(date),\
            'time'     : data2BCD(time),\
            'flags'    : byte2array(ord(flags)),\
            'id'       : data2BCD(id),\
            'model'    : ord(model),\
            'version'  : version[0]+"."+version[1],\
            'mode'     : byte2tet(ord(mode)),\
            'check'    : data2BCD(check),\
            'smena'    : data2int(smena,0,2),\
            'stcheck'  : byte2array(ord(stcheck)),\
            'sumcheck' : data2BCD(sumcheck),\
            'floatdec' : ord(floatdec),\
            'port'     : ord(port)\
        }
        self.sflags ={}
        for k,v in FLAGS_STATUS.items():
            self.sflags[k]=self.status['flags'][v[0]]
        return True

    def _typedev(self):
        self._send_command("typedev","")
        if self._iserror(11):
            return
        (error,proto,type_dev,model,mode,ver) = data2bufs(self.answer,[1,1,1,1,2,5])
        self.device={\
            'proto'     : ord(proto),\
            'type'      : ord(type_dev),\
            'model'     : ord(model),\
            'mode'      : [ord(mode[0]),ord(mode[1])],\
            'ver'       : data2BCD(ver),\
            'name'      : self.answer[11:]\
            }

    def _readreg(self,regname):
        (reg,param1,param2,sizes) = REGISTERS[regname]
        self._send_command("readreg",reg+param1+param2)
        if self._iserror(2):
            return
        return data2bufsBCD(self.answer[2:],sizes)
        
    """ Программировние
        =====================================================================================
    """

    def _setdate(self,D,M,Y):
        data=BCD2data(D)+BCD2data(M)+BCD2data(Y)
        self._send_command("setdate",data)

    def _settime(self,H,M,S):
        data=BCD2data(H)+BCD2data(M)+BCD2data(S)
        self._send_command("settime",data)

    def prn_setcurtime(self):
        t=time.localtime()
        self._settime(str(t.tm_hour),str(t.tm_min),str(t.tm_sec))

    def prn_setcurdate(self):
        t=time.localtime()
        self._setdate(str(t.tm_mday),str(t.tm_mon),str(t.tm_year-2000))

    def _renull(self):
        self._exitmode()
        if not self._setmode("select",self.admpassword):
            return
        self._send_command("renull","")

    def _defaulttabs(self):
        self._exitmode()
        if not self._setmode("select",self.admpassword):
            return
        self._send_command("defaulttabs","")

    def _setmode_prog(self):
        self._exitmode()
        if not self._setmode("prog",self.admpassword):
            return False
        else:
            return True

    """ Установка любого одного значения таблицы """
    def _settabvalue(self,value,tab,row,field):
        data=chr(tab)+int2data(row,2)+chr(field)+value
        self._send_command("settabvalue",data)

    """ Чтение любого одного элемента таблицы """
    def _gettabvalue(self,tab,row,field):
        data=chr(tab)+int2data(row,2)+chr(field)
        self._send_command("gettabvalue",data)
        if self.error!=CMDERR_NO:
            return "0"
        return self.answer[2:]

    def prn_tabset(self,value="",tabval="",incrow=0,nvalues=1):
        if not TABLE_VALUES.has_key(tabval):
            self.error=CMDERR_LN
            return {}
        (tab,row,field,_type) = TABLE_VALUES[tabval]
        row+=incrow
        if nvalues==1:
            value=[value]
        for l in range(nvalues):
            if self.error!=CMDERR_NO:
                continue
            if _type=='BCD':
                val=BCD2data(value[l])
            else:
                val=data2fpcode(value[l].ljust(self.MAX_WIDTH,' '))
            self._settabvalue(val,tab,row+l,field)
        

    """ Чтение одного или нескольких параметров таблиц по названию """    
    def prn_tabgets_CHR(self,tabval="",incrow=0,nvalues=1):
        if not self._setmode_prog():
            return {}
        if not TABLE_VALUES.has_key(tabval):
            self.error=CMDERR_LN
            return {}
        (tab,row,field,_type) = TABLE_VALUES[tabval]
        row+=incrow
        result=[]
        for l in range(nvalues):
            value=self._gettabvalue(tab,row+l,field)
            if self.error!=CMDERR_NO:
                continue
            if _type=='BCD':
                result.append(data2BCD(value))
            else:
                result.append(fpcode2txt(value))
        self._exitmode()
        self.tabvalues=result
        return result

    """ Чтение всех BCD значений таблиц """
    def prn_tabgets_BCD(self):
        if not self._setmode_prog():
            return {}
        result={}
        for v in TABLE_VALUES.keys():
            (tab,row,field,_type) = TABLE_VALUES[v]
            if _type=='BCD':
                value=data2BCD(self._gettabvalue(tab,row,field))
                result[v]=value
        self._exitmode()
        self.tabvalues=result
        return result
    

    """ РЕГИСТРАЦИЯ
        =====================================================================================
    """

    def _opensmena(self,text=u""):
        if not self._setmode("reg",self.admpassword):
            return
        data=chr(0)+text.encode('cp866')
        self._send_command("opensmena",data)

    def _opencheck(self,_type):
        if not self._setmode("reg",self.admpassword):
            self._cancelcheck()
            if not self._setmode("reg",self.admpassword):
                return
        if type(_type)==str:
            _type=TYPE_CHECK[_type]
        else:
            _type=chr(_type)
        data=NULL+_type
        self._send_command("opencheck",data)
        if self._iserror():
            self._cancelcheck()
            self._send_command("opencheck",data)

    def _cancelcheck(self):
        self._send_command("cancelcheck","")
        self._exitmode()

    def _register(self,price="0",count="0",section="1"):
        data=NULL+sval2data(price,5)+sval2data(count,5)+sval2data(section,1)
        self._send_command("register",data)

    def _return(self,price="0",count="0",nocheck=1):
        nc=str(nocheck)
        flags=chr(int("0%s000000" % nc,2))
        data=flags+sval2data(price,5)+sval2data(count,5)
        self._send_command("return",data)

    def _registerpos(self,title,price="0",count="0",tdiscount="0",znak="0",size="0",nalog="4",section="1",shk=""):
        if shk=="":
            shk=NULL*16
        tdiscount=chr(int(tdiscount))
        znak=chr(int(znak))
        nalog=chr(int(nalog))
        data=NULL+title.encode('cp866').ljust(64,NULL)+sval2data(price,6)+sval2data(count,5)+tdiscount+znak+sval2data(size,6)+nalog+sval2data(section,1)+shk.ljust(16,NULL)+NULL
        self._send_command("registerpos",data)

    def _returnpos(self,title,price="0",count="0",tdiscount="0",znak="0",size="0",nalog="4",section="1",shk=""):
        if shk=="":
            shk=NULL*16
        tdiscount=chr(int(tdiscount))
        znak=chr(int(znak))
        nalog=chr(int(nalog))
        data=NULL+title.encode('cp866').ljust(64,NULL)+sval2data(price,6)+sval2data(count,5)+tdiscount+znak+sval2data(size,6)+nalog+sval2data(section,1)+shk.ljust(16,NULL)+NULL
        self._send_command("returnpos",data)

    def _incash(self,sumBCD):
        self._exitmode()
        if not self._setmode("reg",self.admpassword):
            return
        data=NULL+sval2data(sumBCD,5)
        self._send_command("incash",data)

    def _outcash(self,sumBCD):
        self._exitmode()
        if not self._setmode("reg",self.admpassword):
            return
        data=NULL+sval2data(sumBCD,5)
        self._send_command("outcash",data)

    def _discount(self,lastposition=0,issum=1,isgrow=0,value="0"):
        if issum==1:
            val=sval2data(value,5)
        else:
            val=sval2data(value,3)
        data=NULL+chr(lastposition)+chr(issum)+chr(isgrow)+val
        self._send_command("discount",data)

    def _closecheck(self,paytype,summa):
        data=NULL+chr(paytype)+sval2data(summa,5)
        self._send_command("closecheck",data)
        time.sleep(tmC)
        self._exitmode()
    
    """ Отчеты
        =====================================================================================
    """

    def _reportX(self,type_report):
        self._exitmode()
        if not self._setmode('otx',self.admpassword):
            return
        data=chr(type_report)
        self._send_command("reportX",data)
        time.sleep(tmX)
        self._exitmode()
        
    def _reportZ(self):
        self._exitmode()
        if not self._setmode("otz",self.admpassword):
            return
        self._send_command("reportZ","")
        time.sleep(tmZ)
        self._exitmode()

    """ Высокоуровневые методы. 
        Упрощение печати Линия, Русунок, QR, Промотка, Печать в несколько строк
        =====================================================================================
    """

    def prn_devstatus(self):
        r_inn=self._readreg('inn')
        r_eklz=self._readreg('eklz')
        r_width=self._readreg('width')
        r_sum=0
        r_vir=0
        #r_sum=self._readreg('sum')
        #r_vir=self._readreg('vir')
        self._typedev()
        self._status()
        self._codestatus()
        try:
            self.DEVICE = {
                'dev_id'        : self.status['id'],\
                'dev_name'      : fpcode2txt(self.device['name']),\
                'dev_model'     : self.device['model'],\
                'dev_ver'       : self.device['ver'],\
                'dev_mode'      : self.status['mode'],\
                'dev_versoft'   : self.status['version'],\
                'dev_wchar'     : int(r_width[0]),\
                'dev_wpix'      : int(r_width[1]),\
                'dev_floatdec'  : self.status['floatdec'],\
                'dt_date'       : BCD2date(self.status['date']),\
                'dt_time'       : BCD2date(self.status['time']),\
                'dev_sport'     : self.status['port'],\
                'f_closebox'    : self.sflags['f_closebox'],\
                'f_opencap'     : self.sflags['f_opencap'],\
                'f_ispaper'     : self.sflags['f_ispaper'],\
                'f_easypower'   : self.sflags['f_easypower'],\
                'f_fiskal'      : self.sflags['f_fiskal'],\
                'f_opensm'      : self.sflags['f_opensm'],\
                'fc_nocut'      : self.csflags['fc_nocut'],\
                'fc_notpaper'   : self.csflags['fc_notpaper'],\
                'fc_hot'        : self.csflags['fc_hot'],\
                'fc_braked'     : self.csflags['fc_braked'],\
                'c_check'       : self.status['check'],\
                #'c_sum'         : BCD2sval(r_sum[0],2),\
                #'c_vir'         : BCD2sval(r_vir[1],2),\
                'n_inn'         : r_inn[0],\
                'n_rnm'         : r_inn[1],\
                'n_dtfiskal'    : BCD2date(r_inn[3]),\
                'n_ideklz'      : r_eklz[0],\
                'n_dteklz'      : BCD2date(r_eklz[1]),\
                }
            self.MAX_WIDTH=self.DEVICE['dev_wchar']
            self.MAX_PIXELS_WIDTH=self.DEVICE['dev_wpix'] 
        except:
            if self.error==CMDERR_NO:
                self.error=CMDERR_LN

    """ Линия символов """
    def prn_line(self,ch):
        self._print(ch*self.MAX_WIDTH)

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
                #if _type=='sale':
                """ 2.0.69 Теперь регистрация позиции в любом случае """
                self._registerpos(title,realcena,p2,section=section)
                #else:
                    #self._returnpos(title,realcena,p2,section=section)
            else:
                if _type=='sale':
                    self._register(p1,p2,section=section)
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
        self.prn_lines(s,height=1,font=0,big=True)
        self.prn_sale_style(text=u"НАЛИЧНЫМИ",val="="+nal,ch=ch)
        self.prn_sale_style(text=u"БЕЗНАЛИЧНЫМИ",val="="+bnal,ch=ch)
        self.prn_sale_style(text=u"СДАЧА",val="="+sdacha,ch=ch)

    def prn_sale_head(self,ncheck,dt,tm):
        self.prn_sale_style(text="#"+ncheck,val=dt+" "+tm,ch=" ")


    """ Комплексный метод печати. Текст с переносом на следующую строку, признаком крупного текста, настройками стиля"""
    def prn_lines(self,text="",width=0,big=False,font=0,height=0,bright=0,invert=0,align='left'):
        if big:
            text=txt2bigtxt(text)
        if width==0:
            width=self.MAX_WIDTH
        if invert==1:
            style=[1,1,1]
        else:
            style=[0,0,0]
        atext=text.split("\n")
        for s in atext:
            while len(s)>0:
                if len(s)>width:
                    t=s[:width]
                    s=s[width:]
                else:
                    t=s
                    s=""
                if align=='centers':
                    m=self.MAX_WIDTH
                    t=t.center(m," ")
                self._printf(text=t,font=font,height=height,bright=bright,style=style)

    """ Промотка """
    def prn_roll(self,n=4):
        for i in range(n):
            self.prn_line(" ")

    def _print_image(self,im,_retry,_margin):
        if im.size[0] > self.MAX_PIXELS_WIDTH:
            return False
        if im.size[1] > self.MAX_PIXELS_HEIGHT:
            return False

        img_size=[0,0]
        img_size[0] = (im.size[0]//8)*8
        img_size[1] = im.size[1]

        line = convert_image(im,img_size)

        img_bytes_width=img_size[0]/8
        for y in range(img_size[1]):
            buffer = ""
            for x in range(img_bytes_width):
                s = line[(y*img_size[0]+x*8):(y*img_size[0]+x*8+8)]
                buffer += "%02X" % int(s,2)
            dataline=buffer.decode("hex")
            self._printim(retry=_retry,margin=_margin,data=dataline)

    def prn_image(self,path_img="",retry=1,margin=0):
        """print image file """
        im_open = Image.open(path_img)
        im = im_open.convert("RGB")
        self._print_image(im,retry,margin)


    def prn_qr(self, text, *args, **kwargs):
        """ Print QR Code for the provided string """
        qr_args = dict(
            version=4,
            box_size=5,
            border=1,
            error_correction=qrcode.ERROR_CORRECT_M
        )

        qr_args.update(kwargs)
        qr_code = qrcode.QRCode(**qr_args)

        qr_code.add_data(text)
        qr_code.make(fit=True)
        qr_img = qr_code.make_image()
        im = qr_img._img.convert("RGB")
        self._print_image(im,1,0)

    def prn_print_status(self):
        keys = self.DEVICE.keys()
        keys.sort()
        self.prn_line("*")
        for k in keys:
            fprint._print( "%s  -  %s" %(k,fprint.DEVICE[k]))
        tv=self.prn_tabgets_BCD()
        keys = tv.keys()
        keys.sort()
        self.prn_line("*")
        for k in keys:
            self._print( "%s  -  %s" %(k,tv[k]))
        self.prn_line("_")
        self.prn_roll(10)

    """ Тесты
        =====================================================================================
    """

    def prn_test(self):
        self.prn_line("~")
        for i in range(5):
            self._printf(text=u"Тест шрифта номер [%d]" % i,font=i)
        self.prn_line("-")
        for i in (0,1,3):
            self._printf(text=u"Тест множителя номер [%d]" % i,height=i)
        self.prn_line("-")
        for i in range(16):
            self._printf(text=u"Тест яркости номер [%d]" % i,bright=i)
        self.prn_line("-")
        self._printf(text=u"Тест стилей ОБЫЧНЫЙ ТЕКСТ",style=[0,0,0])
        self._printf(text=u"Тест стиле Стильный ТЕКСТ" ,style=[1,1,1])
        self.prn_line("=")
        self.prn_roll(5)
        self.prn_lines(text=u"12345678901234567890123456789012345678901234567890",big=False,font=3,height=1,bright=1,style=[0,0,0])
        self.prn_lines(text=u"12345678901234567890123456789012345678901234567890",big=True,font=0,height=0,bright=2,style=[0,0,0])
        self._cut(True)

    """ Демонстрация проигрывания мелодии """
    def prn_sound_dartweider(self):
        self._sound(212,60)
        self._sound(212,60)
        self._sound(212,60)
        self._sound(155,40)
        self._sound(233,20)
        self._sound(212,60)
        self._sound(155,40)
        self._sound(233,20)
        self._sound(212,60)

    def prn_test_status(self):
        self._status()
        self._typedev()
        self._codestatus()
        getsum=self._getsum()
        r_deviceid=self._readreg('deviceid')
        r_inn=self._readreg('inn')
        r_eklz=self._readreg('eklz')
        r_width=self._readreg('width')
        r_ncheck=self._readreg('ncheck')
        r_datetime=self._readreg('datetime')
        r_sum=self._readreg('sum')
        r_vir=self._readreg('vir')

        print "DEVICE:\n"+"-"*40
        for k,v in self.device.items():
            print "%s\t: %s" % (k,v)
        print "STATUS:\n"+"-"*40
        for k,v in self.status.items():
            print "%s\t: %s" % (k,v)
        print "STATUS_FLAGS:\n"+"-"*40
        for k,v in self.sflags.items():
            print "%s\t: %s" % (k,v)
        print "CODESTATUS_FLAGS:\n"+"-"*40
        for k,v in self.csflags.items():
            print "%s\t: %s" % (k,v)
        print "GETSUM:\n"+"-"*40
        print getsum
        print "-"*40
        print "REGISTERS:\n"+"-"*40
        print "deviceid:"
        print r_deviceid
        print "inn:"
        print r_inn
        print "eklz:"
        print r_eklz
        print "width:"
        print r_width
        print "ncheck:"
        print r_ncheck
        print "datetime:"
        print r_datetime
        print "sum:"
        print r_sum
        print "vir:"
        print r_vir

    def prn_test_image(self):
        self.prn_image(path_img="IceCash.png",margin=40)
        self.prn_qr("https://www.google.ru/")

    def prn_test_cash(self):
        self._opensmena(u"Смена открыта")
        self._incash("500.00")
        self._outcash("500.00")
        print self.error

    def prn_test_sale(self):
        self._opencheck("sale")
        print "open check:%d" % self.error
        self._print(u"Колбаски копченые")
        self._register("140.52","1.252","1")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.252","1")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.500","2")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.500","2")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.500","2")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.500","2")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.500","2")
        self._discount(issum=0,value="2000")
        self._closecheck(1,"1000000")
        print "result closecheck = %d" % self.error
        return

        self._opencheck("sale")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.252","1")
        self._print(u"Колбаски копченые")
        self._register("140.52","1.500","2")
        self._discount(issum=1,value="2000")
        self._closecheck(2,"0")
        print "result closecheck = %d" % self.error

    def prn_test_return(self):
        fprint._printsh()
        self._opencheck("retsale")
        self._print(u"Колбаски копченые")
        self._return("140.52","1.252")
        self._print(u"Колбаски копченые")
        self._return("140.52","1.500")
        self._discount(issum=0,value="2000")
        self._closecheck(1,"0.00")

        self._opencheck("retsale")
        self._print(u"Колбаски копченые")
        self._return("140.52","1.252")
        self._print(u"Колбаски копченые")
        self._return("140.52","1.500")
        self._discount(issum=1,value="2000")
        self._closecheck(2,"0.00")

    def prn_test_fmt_check(self):       
        self.prn_line("-")
        self.prn_lines(u"Мясные продукты \"Волклва\"\nКолбасы\nКолбаса \"Вятская особая, без консервантов\" ГОСТ. Содержание мяса не менее 100%, 50 грамм в подарок.")
        self.prn_sale_style(u"Цена","327.50",ch=".")
        self.prn_sale_style(u"Количество","4",ch=".")
        self.prn_sale_style(u"Стоимость","1310",ch=".")
        self.prn_line("=")

"""
fprint = KKM_FPRINT(echo=True,port=5555,speed=115200,ip='192.168.137.122')
if not fprint.connect():
    print "error connect"
    sys.exit(1)
fprint._cancelcheck()
fprint.disconnect()
#fprint._opensmena(u"Смена открыта")
#fprint.prn_test()
#fprint.prn_test_fmt_check()
"""

""" THE END
    ================================================================================ 
fprint = KKM_FPRINT(echo=True,port=5555,speed=115200,ip='192.168.137.122')
if not fprint.connect():
    print "error connect"
    sys.exit(1)
#fprint.prn_devstatus()
#fprint.prn_roll(8)
#fprint.prn_sound_dartweider()
#fprint._beep()
#fprint._reportZ()
#fprint._printcode(t=2,text=u"42220139998")
fiscal=1
oper='retsale'
fprint._opencheck("retsale")
#fprint.prn_lines(u"Грос Фаер Голд светлое фильтрованное 11% 4%")
fprint.prn_sale_short(fiscal,u"Грос Фаер Голд светлое фильтрованное 11% 4%",oper,"1","1440.52","2.251","3242.61"," ","5.60","","-")
fprint._closecheck(1,"0.00")
#fprint._closecheck(1,"3242.61")
fprint.disconnect()
fprint = KKM_FPRINT(echo=False,port="/dev/ttyUSB0",speed=115200)
#fprint._opensmena(u"Смена открыта")
#fprint.prn_test()
#fprint.prn_test_fmt_check()
#fprint._cancelcheck()
#fprint._reportZ()

#fprint._opencheck("retsale")
#fprint.prn_test_return()
fiscal=0
oper='return'
fprint.prn_lines(u"Грос Фаер Голд светлое фильтрованное 11% 4%")
fprint.prn_sale_short(fiscal,oper,"1","1440.52","2.251","3242.61"," ","5.60","","-")
fprint.prn_lines(u"Живое светлое")
fprint.prn_sale_short(fiscal,oper,"1","1440.52","2.251","3242.61"," ","","28.40","-")
fprint.prn_lines(u"Чешское нефильтрованное Бочкарев")
fprint.prn_sale_short(fiscal,oper,"1","1440.52","2.251","3242.61"," ","-20.30","10.80","-")
fprint.prn_sale_itog(vsego="9727.83",discount="600.00",itogo="9127.83",nal="9727.83",bnal="0.00",sdacha="600.00",ch=" ")
fprint.prn_sale_head("9290","2016-04-07","16:47")
fprint._cut(True)
fprint._printsh()

#fprint._discount(issum=1,value="600.00")
#fprint._closecheck(1,"0.00")

#fprint._closecheck(1,"9727.83")
#fprint.prn_sound_dartweider()
#print fprint.DEVICE
#values=fprint.prn_tabgets_CHR(tabval="textlines",incrow=0,nvalues=20)
#fprint._setmode_prog()
#fprint.prn_tabset(value="08",tabval="speed",incrow=0,nvalues=1)
#fprint._exitmode()

#print fprint.error
#print values
fprint.disconnect()
"""
