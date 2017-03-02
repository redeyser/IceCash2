#!/usr/bin/python
import sys,os,xmpp,time                                                                                                                                                                                                                        
                                                                                                                                                                                                                                               
username = 'bot@beer/sender'
passwd = 'bot123'          
                                                                                                                                                                                                                                               
to=sys.argv[1]               
msg=""                      
line = sys.stdin.readline()    
while line:                   
    msg=msg+line                
    line = sys.stdin.readline()  
                                                                                                                                                                                                                                               
m = sys.stdin.readlines() 
msg.decode('utf8')    
                        
to=to.split(",")                       
jid = xmpp.JID(username) 

client = xmpp.Client(jid.getDomain(),debug=[])
con=client.connect()                        
if not con:                                
    print 'could not connect!'            
    sys.exit()                           
auth=client.auth(jid.getNode(), passwd, 'isendler') 
if not auth:                                                                                                                                                                                                                                   
    print 'could not connect!'                     
    sys.exit()                                    
print "auth.",auth                               
client.sendInitPresence()                       
for n in to:
    client.send(xmpp.Message(n,msg))              
client.disconnect()
