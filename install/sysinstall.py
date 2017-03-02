import os,sys,re
if len(sys.argv)==1:
    print "add param1"
    sys.exit()
path=sys.argv[1]
prog=sys.argv[2]
d=os.getcwd()
f=open(path+"/sysinstall.service","r")
fw=open("/etc/systemd/system/%s.service" % prog,"w")
lines=f.readlines()
for l in lines:
    r=re.search("WorkingDirectory",l)
    if r!=None:
        l="WorkingDirectory=%s\n" % d
    r=re.search("Description",l)
    if r!=None:
        l="Description=%s\n" % prog
    r=re.search("ExecStart",l)
    if r!=None:
        p="/bin/sh "+d+"/start.sh"
        l="ExecStart=%s\n" % p
    fw.write(l)
f.close()
#os.system("ln -s /etc/systemd/system/%s /etc/systemd/system/multi-user.target.wants/%s.service" % (prog,prog))
#os.system("systemctl enable %s.service" % prog)
#os.system("systemctl start %s.service" % prog)
