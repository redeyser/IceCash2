#!/usr/bin/python
# -*- coding: utf8 -*-
"""
Shtrikh FR-K Python interface
=================================================================
Copyright (C) 2010  Dmitry Shamov demmsnt@gmail.com

Redeyser FR-K Python interface
=================================================================
Переработанный драйвер под общий вид с fprint
"""
VERSION = '2.0.029'
PORT = '/dev/ttyS0' #'COM1'
#Commands
DEBUG = 0
TODO  = 1
OS_CP = 'cp866'
MAXWIDTH = 48
MAX_PIXELS_HEIGHT=200
TYPE_CHECK = {\
    'sale'      : chr(0x0),\
    'buy'       : chr(0x1),\
    'retsale'   : chr(0x2),\
    'retbuy'    : chr(0x3),\
    }

def dbg(*a):
        if DEBUG:
                print unicode(string.join(map(lambda x: str(x),a)),'utf8').encode(OS_CP)

def todo(*a):
        if TODO:
                print unicode(string.join(map(lambda x: str(x),a)),'utf8').encode(OS_CP)

import serial
import string,time
from struct import pack, unpack


def bufStr(*b):
    """Преобразует буфер 16-х значений в строку"""
    result = []
    for x in b: result.append(chr(x))
    return string.join(result,'')

def hexStr(s):
    """Преобразуем в 16-е значения"""
    result = []
    for c in s: result.append(hex(ord(c)))
    return string.join(result,' ')

def data2int(d,n,m):
    result=0
    s=0
    for x in range(m):
        c=ord(d[n+x])
        result=result+c*256**s
        s=s+1
    return result

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
    #result.reverse()
    #for i in result:
    #    print hexStr(i)
    return string.join(result,'').rjust(r,NULL)

""" Функции конвертации """
def float2100int(f,digits=2):
        mask = "%."+str(digits)+'f'
        s    = mask % f
        return int(s.replace('.',''))

""" Убрать десятичную точку, добить нулями и перевести в строку данных"""
def sval2data(s,n,_type="i"):
    if n == 1:
        _type='b'
    d=int(s.replace(".","").rjust(n,'0'))
    #print s.replace(".","").rjust(n,'0')
    #print hexStr(pack(_type,d).ljust(5,chr(0x0)))
    return pack(_type,d).ljust(n,chr(0x0))

#Status constants
OK            = 0
KKM_READY     = 1
KKM_ANSWERING = 2
#FP modes descriptions
FP_MODES_DESCR = { 0:u'Принтер в рабочем режиме.',\
                   1:u'Выдача данных.',\
                   2:u'Открытая смена, 24 часа не кончились.',\
                   3:u'Открытая смена, 24 часа кончились.',\
                   4:u'Закрытая смена.',\
                   5:u'Блокировка по неправильному паролю налогового инспектора.',\
                   6:u'Ожидание подтверждения ввода даты.',\
                   7:u'Разрешение изменения положения десятичной точки.',\
                   8:u'Открытый документ:',\
                   9:u'''Режим разрешения технологического обнуления. В этот режим ККМ переходит по включению питания, если некорректна информация в энергонезависимом ОЗУ ККМ.''',\
                   10:u'Тестовый прогон.',\
                   11:u'Печать полного фис. отчета.',\
                   12:u'Печать отчёта ЭКЛЗ.',\
                   13:u'Работа с фискальным подкладным документом:',\
                   14:u'Печать подкладного документа.',\
                   15:u'Фискальный подкладной документ сформирован.'}

FR_SUBMODES_DESCR = {0:{0:u'Подрежим не предусмотрен'},\
                     1:{0:u'Подрежим не предусмотрен'},\
                     2:{0:u'Подрежим не предусмотрен'},\
                     3:{0:u'Подрежим не предусмотрен'},\
                     4:{0:u'Подрежим не предусмотрен'},\
                     5:{0:u'Подрежим не предусмотрен'},\
                     6:{0:u'Подрежим не предусмотрен'},\
                     7:{0:u'Подрежим не предусмотрен'},\
                     8:{0:u'Продажа',\
                        1:u'Покупка',\
                        2:u'Возврат продажи',\
                        3:u'Возврат покупки'},\
                     9:{0:u'Подрежим не предусмотрен'},\
                     10:{0:u'Подрежим не предусмотрен'},\
                     11:{0:u'Подрежим не предусмотрен'},\
                     12:{0:u'Подрежим не предусмотрен'},\
                     13:{0:u'Продажа (открыт)',\
                        1:u'Покупка (открыт)',\
                        2:u'Возврат продажи (открыт)',\
                        3:u'Возврат покупки (открыт)'},\
                     14:{0:u'Ожидание загрузки.',\
                         1:u'Загрузка и позиционирование.',\
                         2:u'Позиционирование.',\
                         3:u'Печать.',\
                         4:u'Печать закончена.',\
                         5:u'Выброс документа.',\
                         6:u'Ожидание извлечения.'},\
                     15:{0:u'Подрежим не предусмотрен'}}


NULL= chr(0x00)
ENQ = chr(0x05)
STX = chr(0x02)
ACK = chr(0x06)
NAK = chr(0x15)

MAX_TRIES = 10 # Кол-во попыток
MIN_TIMEOUT = 0.05
T1 = 0.5
T5 = 12

# Две секунды ждем после оплаты чека, пока он допечатается. 
# Только потом принимаем новые запросы
TIMEOUT_AFTER_CLOSECHECK = 2

DEFAULT_ADM_PASSWORD = bufStr(0x1e,0x0,0x0,0x0) #Пароль админа по умолчанию = 30
DEFAULT_PASSWORD     = bufStr(0x1,0x0,0x0,0x0)  #Пароль кассира по умолчанию = 1

def LRC(buff):
    """Подсчет CRC"""
    result = 0
    for c in buff:
        result = result ^ ord(c)
    #dbg( "LRC",result)
    return chr(result)

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


#Exceptions
class kkmException(Exception):
        def __init__(self, value):
                self.value = value
                self.s = { 0x4e: "Смена превысила 24 часа (Закройте смену с гашением) (ошибка 0x4e)",\
                           0x4f: "Неверный пароль (ошибка 0x4f)",\
                           0x73: "Команда не поддерживается в данном режиме (отмените печать чека или продолжите её или закончилась смена, надо осуществить гашение.) (ошибка 0x73)",
                        }[value]
        def __str__(self):
            return self.s

        def __unicode__(self):
            return unicode(str(self.s),'utf8')
#commands
class KKM:
        def __init__(self,conn,password=DEFAULT_PASSWORD,wide=MAXWIDTH):
                self.conn     = conn
                self.password = password
                self.MAX_WIDTH=wide
                if self.__checkState()!=NAK:
                        buffer=''
                        while self.conn.inWaiting():
                                buffer += self.conn.read()
                        self.conn.write(ACK+ENQ)
                        if self.conn.read(1)!=NAK:
                                raise RuntimeError("NAK expected")

        def __checkState(self):
                """Проверить на готовность"""
                self.conn.write(ENQ)
                repl = self.conn.read(1)
                if not self.conn.isOpen():
                        raise RuntimeError("Serial port closed unexpectly")
                if repl==NAK:
                        return NAK
                if repl==ACK:
                        return ACK
                raise RuntimeError("Unknown answer")

        def __clearAnswer(self):
                """Сбросить ответ если он болтается в ККМ"""
                def oneRound():
                        self.conn.flush()
                        #time.sleep(MIN_TIMEOUT*10)#doom_changed Втр Май 19 09:51:04 NOVT 2015
                        self.conn.write(ENQ)
                        a = self.conn.read(1)
                        #time.sleep(MIN_TIMEOUT*2)#doom_changed Втр Май 19 09:51:13 NOVT 2015
                        if a==NAK:
                                return 1
                        elif a==ACK:
                                a = self.conn.read(1)
                                time.sleep(MIN_TIMEOUT*2)
                                if a!=STX:
                                        raise RuntimeError("Something wrong")
                                length = ord(self.conn.read(1))
                                time.sleep(MIN_TIMEOUT*2)
                                data = self.conn.read(length+1)
                                self.conn.write(ACK)
                                time.sleep(MIN_TIMEOUT*2)
                                return 2
                        else:
                                raise RuntimeError("Something wrong")
                n=0
                while n<MAX_TRIES and oneRound()!=1:
                        n+=1
                if n>=MAX_TRIES:
                        return 1
                return 0

        # Метод из fprint. Попытка чтения конкретного байта в течении 10 секунд        
        def _read_byte(self,b,max_timeout=T5):
            _continue = True
            timeout=0
            while _continue:
                try:
                    self.answerbyte = self.conn.read (1)
                except:
                    self.answerbyte=""
                if (timeout>max_timeout)or(len(self.answerbyte) > 0):
                    break
                else:
                    time.sleep(T1)
                    timeout=timeout+T1
                    print "timequery: %d" % timeout
            if (b==self.answerbyte):
                return True
            else:
                print "error len="+str(len(self.answerbyte))+",b="+hexStr(b)
                return False

        def __readAnswer(self):
                """Считать ответ ККМ ожидая ответ"""
                """ Обновленный метод чтения ответа.
                    Во первых, читаем в цикле байт ACK потом STX
                    Попытка чтения в течении 10 секунд.
                    То есть ловим ответ в это время, вмето того чтобы тупо спать (sleep)
                """
                if self._read_byte(ACK):
                    if self._read_byte(STX):
                        length   = ord(self.conn.read(1))
                        cmd      = self.conn.read(1)
                        errcode  = self.conn.read(1)
                        data     = self.conn.read(length-2)
                        if length-2!=len(data):
                             self.conn.write(NAK)
                             raise RuntimeError("Length (%i) not equal length of data (%i)" % (length, len(data)))
                        rcrc   = self.conn.read(1)
                        mycrc = LRC(chr(length)+cmd+errcode+data)
                        if rcrc!=mycrc:
                             self.conn.write(NAK)
                             raise RuntimeError("Wrong crc %i must be %i " % (mycrc,ord(rcrc)))
                        self.conn.write(ACK)
                        self.conn.flush()
                        if ord(errcode)!=0:
                             print "KKM EXEPTION:",ord(errcode)
                             #raise kkmException(ord(errcode))
                        return {'cmd':cmd,'errcode':ord(errcode),'data':data}
                    else:
                        print "a!=STX"
                        raise RuntimeError("a!=STX %s %s" % (hex(ord(a)),hex(ord(STX))))
                elif self.answerbyte==NAK:
                    print "NAK"
                    return None
                else:
                    print "a!=ACK"
                    raise RuntimeError("a!=ACK %s %s" % (hex(ord(a)),hex(ord(ACK))))
                    
        def __readAnswerFast_old(self):
            a = self.conn.read(5)
            if a[0]==ACK:
                if a[1]==STX:
                    length  = ord(a[2])
                    cmd      = a[3]
                    errcode  = a[4]
                    if length>0:
                        data  = self.conn.read(length-2)
                        if length-2!=len(data):
                            self.conn.write(NAK)
                            raise RuntimeError("Length (%i) not equal length of data (%i)" % (length, len(data)))
                        rcrc   = self.conn.read(1)
                        mycrc = LRC(chr(length)+cmd+errcode+data)
                        if rcrc!=mycrc:
                            self.conn.write(NAK)
                            raise RuntimeError("Wrong crc %i must be %i " % (mycrc,ord(rcrc)))
                    self.conn.write(ACK)
                    self.conn.flush()
                    if ord(errcode)!=0:
                        print "KKM EXEPTION:",ord(errcode)
                        #raise kkmException(ord(errcode))
                    return {'cmd':cmd,'errcode':ord(errcode),'data':data}
            else:
                return None


        def __readAnswer_old(self):
                """Считать ответ ККМ"""
                a = self.conn.read(1)
                if a==ACK:
                    a = self.conn.read(1)
                    if a==STX:
                         length   = ord(self.conn.read(1))
                         cmd      = self.conn.read(1)
                         errcode  = self.conn.read(1)
                         data     = self.conn.read(length-2)
                         if length-2!=len(data):
                              #print hexStr(data)
                              self.conn.write(NAK)
                              raise RuntimeError("Length (%i) not equal length of data (%i)" % (length, len(data)))
                         rcrc   = self.conn.read(1)
                         mycrc = LRC(chr(length)+cmd+errcode+data)
                         if rcrc!=mycrc:
                              self.conn.write(NAK)
                              raise RuntimeError("Wrong crc %i must be %i " % (mycrc,ord(rcrc)))
                         self.conn.write(ACK)
                         self.conn.flush()
                         time.sleep(MIN_TIMEOUT*2)
                         if ord(errcode)!=0:
                              print "KKM EXEPTION:",ord(errcode)
                              #raise kkmException(ord(errcode))
                         return {'cmd':cmd,'errcode':ord(errcode),'data':data}
                    else:
                        print "a!=STX"
                        raise RuntimeError("a!=STX %s %s" % (hex(ord(a)),hex(ord(STX))))
                elif a==NAK:
                    print "NAK"
                    return None
                else:
                    print "a!=ACK"
                    raise RuntimeError("a!=ACK %s %s" % (hex(ord(a)),hex(ord(ACK))))



        def __sendCommand(self,cmd,params):
                """Стандартная обработка команды"""
                self.conn.flush()
                data   = chr(cmd)+params
                length = 1+len(params)
                #print "length="+str(len(params))
                content = chr(length)+data
                crc = LRC(content)
                self.conn.write(STX+content+crc)
                #dbg(hexStr(STX+content+crc))
                self.conn.flush()
                return OK

        def _beep(self):
                """Гудок"""
                self.__clearAnswer()
                self.__sendCommand(0x13,self.password)
                answer = self.__readAnswer()
                return answer['errcode']

        def getTableStruct(self,number):
                """Request short status info"""
                self.__clearAnswer()
                self.__sendCommand(0x2d,DEFAULT_ADM_PASSWORD + chr(number))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.LAST_ERROR = errcode
                self.TableStruct=[data2int(data,40,2),ord(data[42]),data[0:40]]
                return errcode
                
        def getFieldStruct(self,table,field):
                """Request struct field of table"""
                self.__clearAnswer()
                self.__sendCommand(0x2e,DEFAULT_ADM_PASSWORD + chr(table)+chr(field))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.LAST_ERROR = errcode
                _type=ord(data[40])
                _size=ord(data[41])
                if _type==0:
                    minval=data2int(data,42,_size)
                    maxval=data2int(data,42+_size,_size)
                else:
                    minval=0
                    maxval=0
                self.FieldStruct=[_type,_size,minval,maxval,data[0:40]]
                return errcode

        def shortStatusRequest(self):
                """Request short status info"""
                self.__clearAnswer()
                self.__sendCommand(0x10,self.password)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.LAST_ERROR = errcode
                ba = byte2array(ord(data[2]))
                ba.extend(byte2array(ord(data[1])))
                #dbg("ba=",ba)
                result = {
                                  'operator':                  ord(data[0]), \
                                  'flags':                     data[1]+data[2], \
                                  'mode':                      ord(data[3]),\
                                  'submode':                   ord(data[4]),\
                                  'rull_oper_log':             ba[0],\
                                  'rull_check_log':            ba[1],\
                                  'upper_sensor_skid_document':ba[2],\
                                  'lower_sensor_skid_document':ba[3],\
                                  '2decimal_digits':           ba[4],\
                                  'eklz':                      ba[5],\
                                  'optical_sensor_oper_log':   ba[6],\
                                  'optical_sensor_chek_log':   ba[7],\
                                  'thermo_oper_log':           ba[8],\
                                  'thermo_check_log':          ba[9],\
                                  'box_open':                  ba[10],\
                                  'money_box':                 ba[11],\
                                  'eklz_full':                 ba[14],\
                                  'battaryvoltage':            ord(data[6]),\
                                  'powervoltage':              ord(data[7]),\
                                  'errcodefp':                 ord(data[8]),\
                                  'errcodeeklz':               ord(data[9]),\
                                  'rezerv':                    data[10:] }
                return result

        def statusRequest(self):
                """Request status info"""
                self.__clearAnswer()
                self.__sendCommand(0x11,self.password)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                #print "data len = ",len(data)
                ba = byte2array(ord(data[11]))
                ba.extend(byte2array(ord(data[12])))
                dbg('len of data',len(data))
                result = {'errcode':                   errcode, \
                          'operator':                  ord(data[0]), \
                          'dev_id':                    unpack('i',data[30]+data[31]+data[32]+data[33])[0],\
                          'dev_ver':                   data[1]+data[2],\
                          'dev_versoft':               unpack('i',data[3]+data[4]+chr(0x0)+chr(0x0))[0],\
                          'dev_date':                  '%02i.%02i.20%02i' % (ord(data[5]),ord(data[6]),ord(data[7])),\
                          'dev_flags':                 unpack('i',data[11]+data[12]+chr(0x0)+chr(0x0))[0],\
                          'dev_mode':                  ord(data[13]),\
                          'dev_submode':               ord(data[14]),\
                          'dev_sport':                 ord(data[15]),\
                          'dev_floatdec':              ba[4],\
                          'dt_date':                   '%02i.%02i.20%02i' % (ord(data[23]),ord(data[24]),ord(data[25])),\
                          'dt_time':                   '%02i:%02i:%02i' % (ord(data[26]),ord(data[27]),ord(data[28])),\
                          'c_zal':                     ord(data[8]),\
                          'c_check':                   unpack('i',data[9]+data[10]+chr(0x0)+chr(0x0))[0],\
                          'c_smena':                   unpack('i',data[34]+data[35]+chr(0x0)+chr(0x0))[0],\
                          'n_fp_ver':                  data[16]+data[17],\
                          'n_fp_build':                unpack('i',data[18]+data[19]+chr(0x0)+chr(0x0))[0],\
                          'n_dtfiskal':                '%02i.%02i.20%02i' % (ord(data[20]),ord(data[21]),ord(data[22])),\
                          'n_flags':                   ord(data[29]),\
                          'n_freerecords':            data2int(data,36,2),\
                          'n_reregisters':            ord(data[38]),\
                          'n_regleft':                ord(data[39]),\
                          'n_inn': "%i" % (data2int(data,40,6)),\
                          'n_ideklz':                  ba[5],\
                          'f_ispaper0':                ba[0],\
                          'f_ispaper':                 ba[1],\
                          'f_doc1':                    ba[2],\
                          'f_doc2':                    ba[3],\
                          'fc_paper0':                 ba[6],\
                          'fc_paper':                  ba[7],\
                          'fc_thermo0':                ba[8],\
                          'fc_thermo':                 ba[9],\
                          'f_opencap':                 ba[10],\
                          'f_openbox':                 ba[11],\
                          'n_eklzfull':                ba[14]}
                return result

        def _incash(self,summa):
                """Внесение денег"""
                self.__clearAnswer()
                bin_summ = sval2data(summa,5)
                self.__sendCommand(0x50,self.password+bin_summ)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.DOC_NUM    = unpack('i',data[0]+data[1]+chr(0x0)+chr(0x0))[0]


        def _outcash(self,summa):
                """Выплата денег"""
                self.__clearAnswer()
                bin_summ = sval2data(summa,5)
                self.__sendCommand(0x51,self.password+bin_summ)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                self.DOC_NUM    = unpack('i',data[1]+data[2]+chr(0x0)+chr(0x0))[0]

        def _opencheck(self,ctype):
            if type(ctype)==str:
                ctype=TYPE_CHECK[ctype]
            else:
                ctype=chr(ctype)
            self.__clearAnswer()
            self.__sendCommand(0x8D,self.password+ctype)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode

        def _opensmena(self):
            self.__clearAnswer()
            self.__sendCommand(0xE0,self.password)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode


        def Skidka(self,summa,text=u"",taxes=[0,0,0,0][:]):
            self.__clearAnswer()
            bsumma  = sval2data(summa,5)
            btaxes = "%s%s%s%s" % tuple(map(lambda x: chr(x), taxes))
            btext  = text.encode('cp1251').ljust(40,chr(0x0))
            self.__sendCommand(0x86,self.password+bsumma+btaxes+btext)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode

        def Nadbavka(self,summa,text=u"",taxes=[0,0,0,0][:]):
            self.__clearAnswer()
            bsumma  = sval2data(summa,5)
            btaxes = "%s%s%s%s" % tuple(map(lambda x: chr(x), taxes))
            btext  = text.encode('cp1251').ljust(40,chr(0x0))
            self.__sendCommand(0x87,self.password+bsumma+btaxes+btext)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode

        def _discount(self,lastposition=0,issum=1,isgrow=0,value="0"):
            #print "discount: ",value
            if isgrow==0:
                return self.Skidka(value)
            else:
                return self.Nadbavka(value)

        def _register(self,price="0",count="1",departament="1",text=u"",taxes=[0,0,0,0][:]):
            """ Изменено doom для совместимости с fprint"""
            #print "register",price,count
            self.__clearAnswer()
            bprice=sval2data(price,5)
            bcount=sval2data(count,5)
            bdep=sval2data(departament,1,'b')
            btaxes = "%s%s%s%s" % tuple(map(lambda x: chr(x), taxes))
            btext  = text.encode('cp1251').ljust(self.MAX_WIDTH,chr(0x0))[:self.MAX_WIDTH]
            self.__sendCommand(0x80,self.password+bcount+bprice+bdep+btaxes+btext)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode

        def _return(self,price="0",count="1",departament="1",text=u"",taxes=[0,0,0,0][:]):
            """ Изменено doom для совместимости с fprint"""
            #nprint price,count,departament
            self.__clearAnswer()
            bprice=sval2data(price,5)
            bcount=sval2data(count,5)
            bdep=sval2data(departament,1,'b')
            btaxes = "%s%s%s%s" % tuple(map(lambda x: chr(x), taxes))
            btext  = text.encode('cp1251').ljust(self.MAX_WIDTH,chr(0x0))[:self.MAX_WIDTH]
            self.__sendCommand(0x82,self.password+bcount+bprice+bdep+btaxes+btext)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode

        def _closecheck(self,summa,summa2,discount=0,text=u"",taxes=[0,0,0,0][:]):
            self.__clearAnswer()
            bsumma  = sval2data(summa,5)
            bsumma2 = sval2data(summa2,5)
            bsumma3 = pack('i',float2100int(0))+chr(0x0)
            bsumma4 = pack('i',float2100int(0))+chr(0x0)
            bsale   = pack('h',float2100int(discount))
            btaxes = "%s%s%s%s" % tuple(map(lambda x: chr(x), taxes))
            btext  = text.encode('cp1251').ljust(40,chr(0x0))
            self.__sendCommand(0x85,self.password+bsumma+bsumma2+bsumma3+bsumma4+bsale+btaxes+btext)
            a = self.__readAnswer()
            # Предположительно, ответ приходит раньше чем чек реально допечатается.
            # Возможно, ответ приходит сразу после отправки в ОФД
            time.sleep(TIMEOUT_AFTER_CLOSECHECK) 
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode

        def _preitog(self):
            print "PREITOG!"
            self.__clearAnswer()
            self.__sendCommand(0x89,self.password)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            print "PREITOG ANSWER:",errcode
            self.OP_CODE    = ord(data[0])
            return errcode

        def _reportX(self,admpass):
                """Отчет без гашения"""
                self.__clearAnswer()
                self.__sendCommand(0x40,admpass)
                time.sleep(4)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                print errcode
                return errcode

        def _reportZ(self,admpass):
                """Отчет с гашением"""
                self.__clearAnswer()
                self.__sendCommand(0x41,admpass)
                time.sleep(3)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                print errcode
                a = self.statusRequest()
                return errcode

        def cutCheck(self,cutType):
                """Отрезка чека
                   Команда:     25H. Длина сообщения: 6 байт.
                        • Пароль оператора (4 байта)
                        • Тип отрезки (1 байт) «0» – полная, «1» – неполная
                   Ответ:       25H. Длина сообщения: 3 байта.
                        • Код ошибки (1 байт)
                        • Порядковый номер оператора (1 байт) 1...30
                """
                #self.__clearAnswer()
                if cutType!=0 and cutType!=1:
                   raise RuntimeError("cutType myst be only 0 or 1 ")
                self.__sendCommand(0x25,self.password+chr(cutType))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def continuePrint(self):
                """Продолжение печати
                Команда:    B0H. Длина сообщения: 5 байт.
                        • Пароль оператора, администратора или системного администратора (4 байта)
                   Ответ:      B0H. Длина сообщения: 3 байта.
                        • Код ошибки (1 байт)
                        • Порядковый номер оператора (1 байт) 1...30
                """
                self.__clearAnswer()
                self.__sendCommand(0xB0,self.password)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def repeatDoc(self):
                """Команда:    8CH. Длина сообщения: 5 байт.
                     • Пароль оператора (4 байта)
                Ответ:      8CH. Длина сообщения: 3 байта.
                     • Код ошибки (1 байт)
                     • Порядковый номер оператора (1 байт) 1...30
                     Команда выводит на печать копию последнего закрытого документа
                                 продажи, покупки, возврата продажи и возврата покупки.
                """
                #self.__clearAnswer()
                self.__sendCommand(0x8C,self.password)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def _cancelcheck(self):
                self.__clearAnswer()
                self.__sendCommand(0x88,self.password)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def setDate(self,admpass,day,month,year):
                """Установка даты
                Команда:     22H. Длина сообщения: 8 байт.
                     • Пароль системного администратора (4 байта)
                     • Дата (3 байта) ДД-ММ-ГГ
                Ответ:       22H. Длина сообщения: 2 байта.
                     • Код ошибки (1 байт)
                """
                #print str(day)+"."+str(month)+"."+str(year)
                print "setting date"
                #self.__clearAnswer()
                self.__sendCommand(0x22,admpass+chr(day)+chr(month)+chr(year-2000))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                return errcode

        def acceptSetDate(self,admpass,day,month,year):
                """Установка даты (бред какой-то)
                Команда:     23H. Длина сообщения: 8 байт.
                     • Пароль системного администратора (4 байта)
                     • Дата (3 байта) ДД-ММ-ГГ
                Ответ:       23H. Длина сообщения: 2 байта.
                     • Код ошибки (1 байт)
                """
                #self.__clearAnswer()
                self.__sendCommand(0x23,admpass+chr(day)+chr(month)+chr(year-2000))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                return errcode

        def setTime(self,admpass,hour,minutes,secs):
                """Установка даты
                Команда:    21H. Длина сообщения: 8 байт.
                             • Пароль системного администратора (4 байта)
                             • Время (3 байта) ЧЧ-ММ-СС
                        Ответ:      21H. Длина сообщения: 2 байта.
                             • Код ошибки (1 байт)
                """
                #self.__clearAnswer()
                self.__sendCommand(0x21,admpass+chr(hour)+chr(minutes)+chr(secs))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                return errcode


        def setPort(self,port,speed,timeout):
                self.__sendCommand(0x14,DEFAULT_ADM_PASSWORD+chr(port)+chr(speed)+chr(timeout))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                return  errcode

        def getPort(self,port):
                self.__sendCommand(0x15,DEFAULT_ADM_PASSWORD+chr(port))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.PortSets=[ord(data[0]),ord(data[1])]
                return  errcode

        def getTableValue(self,table,row,field):
                self.getFieldStruct(table,field)
                (f_type,f_size)=(self.FieldStruct[0],self.FieldStruct[1])
                self.__clearAnswer()
                drow    = pack('i',row).ljust(2,chr(0x0))[:2]
                self.__sendCommand(0x1f,DEFAULT_ADM_PASSWORD+chr(table)+drow+chr(field))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                if (f_type==1):
                    self.FieldData=data[0:data[0:40].find("\x00")].rstrip(). decode('cp1251').encode('utf8')
                else:
                    self.FieldData=data2int(data,0,f_size)

                self.FieldStruct.append(self.FieldData)
                return  errcode

        def setTableValue(self,table,row,field,value):
                """Записать значение в таблицу, ряд, поле
                поля бывают бинарные и строковые, поэтому value
                делаем в исходном виде
                """
                self.getFieldStruct(table,field)
                (f_type,f_size)=(self.FieldStruct[0],self.FieldStruct[1])
                if (f_type==0):
                    f_size=f_size+1
                    value=pack('i',int(value)).ljust(f_size,chr(0x0))[:f_size]
                else:
                    value=value.decode('utf8').encode('cp1251').ljust(f_size,' ')

                #self.__clearAnswer()
                #value=chr(0x0)+chr(0x1)
                drow    = pack('i',row).ljust(2,chr(0x0))[:2]
                self.__sendCommand(0x1e,DEFAULT_ADM_PASSWORD+chr(table)+drow+chr(field)+value)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                return  errcode

        def _printsh(self):
                """Напечатать клише"""
                self.__sendCommand(0x52,self.password)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def _print(self,text=u""):
                """Напечатать строку"""
                self.__clearAnswer()
                flag = 0b11
                if self.MAX_WIDTH>=40:
                    MW=self.MAX_WIDTH
                else:
                    MW=40
                s = text.encode('cp1251').ljust(MW,' ')
                self.__sendCommand(0x17,self.password+bufStr(flag)+s)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def _printf(self,text,font):
                """Напечатать строку"""
                self.__clearAnswer()
                flag = 0
                flag = flag | 2
                if len(text)>self.MAX_WIDTH:
                    raise RuntimeError("Length of string myst be less or equal 40 chars")
                if self.MAX_WIDTH>=40:
                    MW=self.MAX_WIDTH
                else:
                    MW=40
                s = text.encode('cp1251').ljust(MW,chr(0x0))
                self.__sendCommand(0x2f,self.password+chr(flag)+chr(font)+s)
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode

        def _printcode(self,shk):
                """Напечатать shk"""
                self.__clearAnswer()
                shk=shk[:12]
                bshk=int(shk)
                bshk=int2data(bshk,5)
                self.__sendCommand(0xC2,self.password+bshk)
                a = self.__readAnswer()
                return a['errcode']

        def loadGraph(self,line,sbits):
                self.__clearAnswer()
                abits=''
                for n in sbits.split(','):
                    abits=abits+chr(int(n))
                cbits = abits.ljust(40,chr(0x0))[:40]
                self.__sendCommand(0xC0,self.password+chr(line)+cbits)
                a = self.__readAnswer()
                return a['errcode']

        def loadGraphLines(self,data):
                self.__clearAnswer()
                abits=''
                line=0
                for b in range(0,len(data),40):
                    bts=data[b:b+40]
                    self.__sendCommand(0xC0,self.password+chr(line)+bts)
                    line+=1
                    a = self.__readAnswer()
                return a['errcode']

        def loadGraphFile(self,nfile):
                self.__clearAnswer()
                fl=open(nfile,"rb")
                data=fl.read(40)
                line=0
                while len(data)!=0:
                    cbits = data.ljust(40,chr(0x0))[:40]
                    #time.sleep(0.5)
                    self.__clearAnswer()
                    self.__sendCommand(0xC0,self.password+chr(line)+cbits)
                    a = self.__readAnswer()
                    data=fl.read(40)
                    line=line+1
                fl.close()
                return a['errcode']

        def printGraph(self,line1,line2):
                """Напечатать graph"""
                self.__clearAnswer()
                self.__sendCommand(0xC1,self.password+chr(line1)+chr(line2))
                a = self.__readAnswer()
                return a['errcode']

        def printLine(self,data):
                """Напечатать line"""
                self.__clearAnswer()
                self.__sendCommand(0xC5,self.password+chr(0)+chr(10)+data)
                a = self.__readAnswer()
                return a['errcode']

        def openbox(self):
                """Открыть ящик"""
                #self.__clearAnswer()
                self.__sendCommand(0x28,self.password+chr(0))
                a = self.__readAnswer()
                return a['errcode']

        def roll(self,n):
                """Протяжка"""
                self.__clearAnswer()
                self.__sendCommand(0x29,self.password+chr(2)+chr(n))
                a = self.__readAnswer()
                return a['errcode']

        def renull(self):
                """Технологическое обнуление"""
                self.__clearAnswer()
                self.__sendCommand(0x16,'')
                a = self.__readAnswer()
                print "renull=",a
                return 0

        def Run(self,check_ribbon=True,control_ribbon=True,doc_ribbon=False,row_count=1):
                """Прогон"""
                self.__clearAnswer()
                flag = 0
                if check_ribbon:
                        flag = flag | 1
                if control_ribbon:
                        flag = flag | 2
                if doc_ribbon:
                        flag = flag | 4
                if row_count not in range(1,255):
                        raise RuntimeError("Line count myst be in 1..255 range")

                self.__sendCommand(0x29,self.password+bufStr(flag,row_count))
                a = self.__readAnswer()
                cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
                self.OP_CODE    = ord(data[0])
                return errcode
                
        def Storno(self,count,price,text=u"",department=1,taxes=[0,0,0,0][:]):
            """Сторно"""
            self.__clearAnswer()
            if len(taxes)!=4:
                   raise RuntimeError("Count of taxes myst be 4")
            for t in taxes:
                if t not in range(0,4):
                   raise RuntimeError("taxes myst be only 0,1,2,3,4")
            bcount = pack('i',float2100int(count,3))+chr(0x0)
            bprice = pack('i',float2100int(price))+chr(0x0) 
            bdep   = chr(department)
            btaxes = "%s%s%s%s" % tuple(map(lambda x: chr(x), taxes))
            btext  = text.encode('cp1251').ljust(self.MAX_WIDTH,chr(0x0))[:self.MAX_WIDTH]
            self.__sendCommand(0x84,self.password+bcount+bprice+bdep+btaxes+btext)
            a = self.__readAnswer()
            cmd,errcode,data = (a['cmd'],a['errcode'],a['data'])
            self.OP_CODE    = ord(data[0])
            return errcode



