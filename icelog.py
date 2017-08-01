#!/usr/bin/python
# -*- coding: utf-8
import datetime
def addLog(fname, msg):
    dt=datetime.datetime.today().strftime("%Y-%m-%d %H:%M:%S")
    f =open(fname,"a")
    f.write(dt+"\n")
    f.write(msg)
    f.write("-"*80+"\n")
    f.close()


