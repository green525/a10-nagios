#!/usr/bin/python

## Import the required modules for our code
import getopt, sys, functools, urllib, urllib2, httplib, ssl, json

## Redefine the SSL Socket code in the ssl module to use TVSv1 by default,
## as the old default of v1.1 is unsupported by the A10.
old_init = ssl.SSLSocket.__init__

@functools.wraps(old_init)
def new_ssl_fix(self, *args, **kwargs):
  kwargs['ssl_version'] = ssl.PROTOCOL_TLSv1
  old_init(self, *args, **kwargs)

## Remap our new SSL code as an in-place replacement to the old code.
ssl.SSLSocket.__init__ = new_ssl_fix

## Define a 'Usage' page which displays details on how to use this code.
def usage():
    print("")
    print("Usage: %s -u <username> -p <password> -h <loadbalancer> [-g <slb_group_id>] [-c <PERCENT>] [-w <PERCENT>] [-P <partition>]" % sys.argv[0])
    print("")
    print("    -u <username>		=> Username to authenticate against the A10")
    print("    -p <password>		=> Password to authenticate against the A10")
    print("    -h <loadbalancer>	=> A10's Hostname or IP to Connect to")
    print("    -g <slb_group_id>	=> Report on statistics for a single SLB Service Group")
    print("    -P <partition>	        => Use a specific partition instead of user's default partition/shared")
    print("    -c <PERCENTAGE>		=> Percentage of remaining active nodes to report Critical Status on")
    print("    -w <PERCENTAGE>		=> Percentage of remaining active node to report Warning Status on")
    print("    -d			=> Enable Debug")
    print("")
    sys.exit(1)

## Parse the arguments a user has given us
try:
    myopts, args = getopt.getopt(sys.argv[1:],"u:p:h:g:c:w:dP:")
except getopt.GetoptError:
    usage()

## Set some initial values for some of our variables, before we potentially
## overwrite them with user options
user, password, loadbalancer, slbgroupid = "", "", "", ""
partition = ""
warn = 80
crit = 50
debug = False

## Iterate over each argument provided by the user, and try to map each one to
## a particular setting or variable we need.
for o, a in myopts:
    if o == '-u':
        user = str(a)
    elif o == '-p':
        password = str(a)
    elif o == '-h':
        loadbalancer = str(a)
    elif o == '-g':
	slbgroupid = str(a)
    elif o == '-c':
        crit = str(a)
    elif o == '-w':
        warn = str(a)
    elif o == '-P':
        partition = str(a)
    elif o == '-d':
        debug = True
    else:
        print("Unknown option: " . str(o))
        print("")
        usage()

## Now we've checked the user's arguments, make sure they've at least given us the basics.
for x in user, password, loadbalancer, slbgroupid:
    if x == "":
        usage()

## do_exit  -- Used for exiting in a 'Nagios Compliant' way later:
def do_exit(state, msg):
    if state == 0:
        condition = "OK"
    elif state == 1:
        condition = "WARNING"
    elif state == 2:
        condition = "CRITICAL"
    else:
        # Assume state = 3
        condition = "UNKNOWN"

    print("%s: %s" % (condition, msg))
    sys.exit(state)


## AUTHENTICATE AGAINST THE LB TO GET A SESSION ID
c = httplib.HTTPSConnection(loadbalancer)
apiurl = "/axapi/v3"
authurl = apiurl + "/auth"
authinfo = { 'credentials': { 'username': user, 'password': password } }
headers = { 'Content-type': 'application/json' }
try:
    c.request("POST", authurl, json.dumps(authinfo), headers)
except Exception, err:
    do_exit(3, "Connection Failed to: https://" + loadbalancer + url + ": " + str(err))

data = json.loads(c.getresponse().read())
# Try and assign the session_id variable from what was returned to us from the LB.
try:
    session_id = data['authresponse']['signature']
    if debug == True:
        print "Session Created. Session ID: " + session_id
# If the data isn't there for assigning (ie. Connection or Auth error) we'll get a KeyError instead.
except KeyError:
    errmsg = "Failed to connect/auth against Loadbalancer %s" % loadbalancer
    do_exit(3, errmsg)

headers['Authorization'] = "A10 " + session_id

# Change active partition
if partition != "":
    c.request("POST", apiurl + "/active-partition/" + partition, "", headers)
    try:
        data = json.loads(c.getresponse().read())
        if data['response']['status'] != 'OK':
            do_exit(1, "Could not change to partition " + partition)
    except KeyError:
        do_exit(3, "Invalid response from Loadbalancer")

# Get status
c.request("GET", apiurl + "/slb/service-group/" + slbgroupid + "/oper", "", headers)
data = json.loads(c.getresponse().read())
try:
    group = data['service-group']['oper']
    print "%s/%s %s %s/%s" % (partition, slbgroupid, group['state'], group['servers_up'], group['servers_total'])
except KeyError:
    print("Invalid data from Loadbalancer %s" % loadbalancer)
    sys.exit(1)

c.request("GET", apiurl + "/logoff")
c.getresponse()
