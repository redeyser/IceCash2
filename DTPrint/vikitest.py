#!/usr/bin/python
# -*- coding: utf8 -*-
# frk object v 2.0.007
import kkmdrv
import serial
import time
from PIL import Image
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

NULL= chr(0x00)
ENQ = chr(0x05)
STX = chr(0x02)
ETX = chr(0x03)
ACK = chr(0x06)
NAK = chr(0x15)
FS = chr(0x1c)

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

def _crc(s):
    #import pdb; pdb.set_trace()
    c=25
    for i in s:
        c^=ord(i)
        sc=(hex(c)).upper()
        r=sc[2:]
    return r

class frk:

    def __init__(self,port,speed):
        self.MAX_WIDTH=MAXWIDTH
        self.password = 'PIRI'
        self.admin_password = 'PIRI'
        self.port = '/dev/ttyACM0'
        self.speed = '57600'

        self.salelines=[]
        self.a_startus=['ready','check','error']
        self.error=0

    def connect(self):
        try:
            self.ser = serial.Serial(self.port, int(self.speed),\
                                 parity=serial.PARITY_NONE,\
                                 stopbits=serial.STOPBITS_ONE,\
                                 timeout=0.2,\
                                 writeTimeout=0.2)
        except:
            return False

        try:
            #self.kkm=kkmdrv.KKM(self.ser,password=self.password,wide=self.MAX_WIDTH)
            #s='RI'+chr(28)+'00'+chr(0x3)
            op1=''
            for i in range(16):
                op1+=FS
            kassir=chr(136)+chr(162)+chr(160)+chr(173)+chr(174)+chr(228)+chr(228)+chr(32)+chr(136)+chr(46)+chr(136)+chr(46)+op1
            s='RI'+chr(0x29)+'21'+kassir+ETX
            path='/home/user/Desktop/WORK/VikiPrint/'
            fn=path+"cmd21.viki"
            f=open(fn,"w")
            crc=_crc(s)
            #import pdb; pdb.set_trace()
            s=STX+'PI'+s+crc #'\x0d\x0a'
            # self.ser.write(ENQ)
            # time.sleep(0.1)
            # ot=self.ser.read(1)
            # t = time.strftime("%d%m%y%H%M%S", time.localtime())
            # bw0='RI&10'+t+ETX
            # crc=_crc(bw0)
            # bw=STX+'PI'+bw0+crc
            # self.ser.write(bw)
            # ot=self.ser.read(1)
            # import pdb; pdb.set_trace()
            #f.write(bw+'\n')
            f.write(s)
            f.close()
            #import pdb; pdb.set_trace()
            self.ser.write(s)
            #time.sleep(0.5)
            err=0
            #self._status_ready()
            print "connect frk"
        except:
            err=const_error
            #self._status_error()
            print "not connect frk"
        return True

#Подключаемся
D=frk('/dev/ttyACM0','57600')
D.connect()
print D.error
