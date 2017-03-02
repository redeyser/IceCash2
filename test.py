#!/usr/bin/python
# -*- coding: utf8 -*-
# IceBonus client v 0.001
import string
import skserv
import sys
import time
import os

sc=skserv.SockClient("10.5.5.1",10100)
print sc.soc
if not sc.soc==None:
    sc.close()
