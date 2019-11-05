#!/usr/bin/python

import sys
import os
import threading
import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from exampleresources import BasicResource

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

temperature_resource = BasicResource()

def get_temp():
    f = open('/sys/bus/w1/devices/28-000007550451/w1_slave')
    lines = f.readlines()
    f.close()
    t_pos = lines[1].find("t=")
    return float(lines[1][t_pos+2:t_pos+6]) / 100

def update_tmp():
    global temperature_resource

    while True:
        temperature_resource.payload = str(get_temp())
        sleep(2)
    

class CoAPServer(CoAP):
    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        global temperature_resource 

        self.add_resource('temperature/', temperature_resource)

        print "CoAP Server start on " + host + ":" + str(port)
        print self.root.dump()

        t = threading.Thread(target=update_tmp, args=())
        t.start()

if __name__ == "__main__":
	server = CoAPServer("0.0.0.0", 5683, False)
    
	try:
		server.listen(10)
	except KeyboardInterrupt:
	        print "Server Shutdown"
	        server.close()
	        print "Exiting..."
