#!/usr/bin/env python2
# -*- coding: utf-8 -*- 
DEBUG = True
import dbus, gobject,re,pynotify,os
from dbus.mainloop.glib import DBusGMainLoop
dingregex = re.compile(r'(ding)',re.IGNORECASE)
def check_ding(account, sender, message, conv, flags):
    sender = sender.encode('utf-8')
    message = message.encode('utf-8')
    obj = bus.get_object("im.pidgin.purple.PurpleService", "/im/pidgin/purple/PurpleObject")
    purple = dbus.Interface(obj, "im.pidgin.purple.PurpleInterface")
    title = purple.PurpleConversationGetTitle(conv).encode('utf-8')
    if not title:
        title = conv
    if len(dingregex.findall(message)) > 0:
        pass
        #pynotify.init("Basics")
        #notify = pynotify.Notification("DING DING DING","{} called for DING DING DING in {}".format(sender,title),"emblem-danger")
        #notify.set_timeout(pynotify.EXPIRES_NEVER)
        #notify.show()
    
    if DEBUG:
        print "sender: {} message: {}, account: {}, conversation: {}, flags: {}, title: {}".format(sender,message,account,conv,flags,title)
    f=open("_","w")
    f.write(message)
    f.close()
    os.system("echo '%s' | python _sendFAX.py localhost 10111 Star +bw" % sender)
    os.system("cat _ | python _sendFAX.py localhost 10111 Star -")
if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    bus.add_signal_receiver(check_ding,
                            dbus_interface="im.pidgin.purple.PurpleInterface",
                            signal_name="ReceivedImMsg")
    loop = gobject.MainLoop()
    loop.run()
