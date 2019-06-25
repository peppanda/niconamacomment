import os
import cookielib
import urllib
import urllib2
import socket
import struct
import re
import time
import requests
from xml.dom import minidom

# Put actual live broadcast live number
# example: https://live2.nicovideo.jp/watch/lv320550733
lvno = "lvXXXXXXXXXXXXX"

# You can find the session ID from the cookie when you logged into the niconico
# https://live.nicovideo.jp/
sid="user_session_XXXXXX_XXXXXXXXXXXXXXXXXXXXXX"

# Gather information from following URL, for address, port, thread id on comment server
apistat_url="http://watch.live.nicovideo.jp/api/getplayerstatus?v=%s"

# user-agent for collection
uagent = "test test"

# Create cookie for access (setup user_session)
cj = cookielib.CookieJar()
ck = cookielib.Cookie(version=0, name='user_session', value=sid, port=None,port_specified=False, domain='.live.nicovideo.jp', domain_specified=False, domain_initial_dot=False, path='/', path_specified=True, secure=False, expires=None, discard=True, comment=None, comment_url=None, rest={'HttpOnly': None}, rfc2109=False)
cj.set_cookie(ck)
opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

# Setup user-agent
opener.addheaders = [('User-agent', uagent)]

# create URL and then access
target_url = apistat_url % lvno
print target_url
r = opener.open(target_url)
data = r.read() #get response from GET(xml format)
r.close()

# original XML
#data2 = data.decode("utf-8")
#print "%s" % data2

# From XML data collect server address, port, thread id
doc = minidom.parseString(data)
child = doc.getElementsByTagName('getplayerstatus')[0]
if child.getElementsByTagName('ms'):
    mstag = child.getElementsByTagName('ms')[0]
    addr = mstag.getElementsByTagName('addr')[0].firstChild.data.strip()
    port = mstag.getElementsByTagName('port')[0].firstChild.data.strip()
    threadid = mstag.getElementsByTagName('thread')[0].firstChild.data.strip()

# get Start_time    
start_time = int(child.getElementsByTagName('start_time')[0].firstChild.data.strip())
print 'start_time = %s' % start_time

# check ThreadID
print 'ThreadID = %s' % threadid

# get postkey
postkeyurl = 'http://ow.live.nicovideo.jp/api/getpostkey?thread=%s&block_no=0' % threadid
r2 = opener.open(postkeyurl)
postkeyread = r2.read()
r2.close()

postkey = postkeyread[8:]
print 'postky = %s' % postkey

# get ticket
#ticketurl = 'https://ow.live.nicovideo.jp/api/getedgestatus?v=%s' % lvno
#r3 = opener.open(ticketurl)
#ticketread = r3.read()
#r3.close()

#ticket = ticketread[187:187+48]
#print 'ticket = %s' % ticket

# check param
print 'addr = %s' % addr
print 'port = %s' % port

#vpos
ts = int(time.time())
print 'current time = %s' % ts

vpos = (ts - start_time)*100
print 'vpos = %s' % vpos

# Create socket, connect with address and port collected earlier
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect((addr, int(port)))

# send embeded thread ID
sd = '<thread thread="%s" version="20061206" res_from="-1"/>' % threadid
sock.send(sd)
sock.send(struct.pack('b',0))

# Ignore first received data
data = sock.recv(2048)

# get ticket ID from first response from server
firstd = data.decode('utf-8')
print 'first received data: %s' % firstd
ticket = firstd[65:65+10]
print 'ticket = %s' % ticket

# create send chat test 
testchat = '<chat thread="%s" ticket="%s" vpos="%s" user_id="12345679" mail="184" postkey="%s" premium="1" locale="jp">testetest</chat>' % (threadid,ticket,vpos,postkey)
print '%s' % testchat



# Receive comment and display
while True:
    data = sock.recv(2048)[:-1]
    datadecode = data.decode("utf-8")
    come = re.sub(r'</?chat.*?>', '', data).decode("utf-8")
    number = re.sub(r'<chat[^>]*no="([0-9]{1,})".*', r'\1', data).decode("utf-8")
    if come == u"/disconnect":
       # When broadcast finish
        break
    else:
       print u"%s: %s" % (number,come)
       print "%s" % datadecode
    
       # Please type anything in the chat, then the code will try to write to the chat
       time.sleep(1)
       sock.send(testchat) #failing at this stage
       break
