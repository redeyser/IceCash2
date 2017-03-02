import usb.core
import usb.util
kbd=usb.core.find(idVendor=0x0749, idProduct=0x1000)
msg="\x00\x00\x00\x00\x00\x00\x00\x00\x00\x11\x00\x01\x00\x00\x00\x01"
interface=0x0
out_ep=0x81
kbd.write(out_ep, msg, interface)
