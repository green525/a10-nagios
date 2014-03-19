#!/usr/bin/python
import getopt, sys, functools
import json, urllib, urllib2
import httplib, ssl

old_init = ssl.SSLSocket.__init__

@functools.wraps(old_init)
def ubuntu_openssl_bug_965371(self, *args, **kwargs):
  kwargs['ssl_version'] = ssl.PROTOCOL_TLSv1
  old_init(self, *args, **kwargs)

ssl.SSLSocket.__init__ = ubuntu_openssl_bug_965371

def usage():
    print("")
    print("Usage: %s -u <username> -p <password> -h <loadbalancer> [-l] [-v <vrrid>] [-c <PERCENT>] [-w <PERCENT>] [-n <NAME>]" % sys.argv[0])
    print("")
    print("-u <username>		=> Username to authenticate against the A10")
    print("-p <password>		=> Password to authenticate against the A10")
    print("-h <loadbalancer>	=> A10's Hostname or IP to Connect to")
    print("-l			=> List available VRRIDS")
    print("-v <vrrid>		=> Report on statistics for a single VRRID")
    print("-c <PERCENTAGE>		=> Percentage of remaining active nodes to report Critical Status on")
    print("-w <PERCENTAGE>		=> Percentage of remaining active node to report Warning Status on")
    print("-n <NAME>		=> Friendly name for the VRRID for alerting.")
    print("")
    sys.exit(1)

# Parse args
try:
    myopts, args = getopt.getopt(sys.argv[1:],"u:p:h:lv:c:w:n:")
except getopt.GetoptError:
    usage()

listonly = False
user, password, loadbalancer, vrrid = "", "", "", ""
warn = 80
crit = 50

for o, a in myopts:
    if o == '-u':
        user = str(a)
    elif o == '-p':
        password = str(a)
    elif o == '-h':
        loadbalancer = str(a)
    elif o == '-l':
        listonly = True
    elif o == '-v':
	vrrid = str(a)
    elif o == '-c':
        crit = str(a)
    elif o == '-w':
        warn = str(a)
    elif o == '-n':
        name = str(a)
    else:
        print("Unknown options: " . str(o))
        print("")
        usage()

for x in user, password, loadbalancer, vrrid:
    if x == "":
        usage()

## Original Code
c = httplib.HTTPSConnection(loadbalancer)
sessionurl = "/services/rest/V2/?method=authenticate&username=%s&password=%s&format=json" % (user, password)
c.request("GET", sessionurl)
response = c.getresponse()
data = json.loads(response.read())
try:
    session_id = data['session_id']
    print "Session Created. Session ID: " + session_id
except KeyError:
    print("Failed Authorization")


#  Step 1. Create Servers     #
###############################
# Create slb servers s1 10.0.2.128
# Construct HTTP URL and Post Body
#post_body = json.dumps(
##{"server":
#{
#"name": "s1",
#"host": "10.0.2.128",
#"health_monitor": "(default)",
#"port_list": [
#{"port_num": 80,
#"protocol": 2,}
#],
#}
#}
#)
#url = "https://172.31.31.121/services/rest/V2/?&session_id=" + session_id + "&format=json&method=slb.server.create"
#print "URL Created. URL: " + url + " body: " + post_body
