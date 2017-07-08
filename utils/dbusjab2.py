#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
DEBUG = True
import dbus, gobject,re,pynotify,os
from dbus.mainloop.glib import DBusGMainLoop
def check_ding(p):
    #print p
    server=p[0]
    sender=p[1][0]
    message=p[1][1]
    sender = sender.encode('utf-8')
    message = message.encode('utf-8')
    f=open("_","w")
    f.write(message)
    f.close()
    os.system("echo '%s' | python _sendFAX.py localhost 10111 Star +bw" % sender)
    os.system("cat _ | python _sendFAX.py localhost 10111 Star -")
if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_signal_receiver(check_ding,
                            dbus_interface="org.gajim.dbus.RemoteInterface",
                            signal_name="NewMessage")
    loop = gobject.MainLoop()
    loop.run()
