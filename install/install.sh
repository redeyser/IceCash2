#!/bin/sh
#cp serialtokbd.py /home/kassir
#chown kassir:kassir /home/kassir/serialtokbd.py
#chmod a+x /home/kassir/serialtokbd.py

apt-get install python-mysqldb python-usb python-qrcode python-requests python-serial

cd pyusb-1.0.0rc1
python setup.py build
python setup.py install
cd ..

cd ../DTPrint
python dbinstall.py
python ../install/sysinstall.py ../install DTPrint

cd ..
python dbinstall.py
python install/sysinstall.py install dIceCash

systemctl enable dIceCash.service
systemctl enable DTPrint.service
systemctl start dIceCash.service
systemctl start DTPrint.service
