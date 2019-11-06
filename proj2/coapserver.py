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
display_resource = BasicResource()

def get_temp():
    f = open('/sys/bus/w1/devices/28-000007550451/w1_slave')
    lines = f.readlines()
    f.close()
    t_pos = lines[1].find("t=")
    return float(lines[1][t_pos+2:t_pos+6]) / 100

def update_temp():
    global temperature_resource

    while True:
        temperature_resource.payload = str(get_temp())
        sleep(2)

def display_resource_listener():
    
    global display_resource
    
    last_display = 2

    while True:
        if display_resource.payload == '1' and last_display == 2:
            print "Display 1"
            last_display = 1
        elif display_resource.payload == '2' and last_display == 1:
            print "Display 2"
            last_display = 2
        
        sleep(1)

class CoAPServer(CoAP):



    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        global temperature_resource
        global display_resource

        self.add_resource('temperature/', temperature_resource)
        self.add_resource('display/', display_resource)
        
        display_resource.payload = '1'
        
        print "CoAP Server start on " + host + ":" + str(port)
        print self.root.dump()

        t_temp = threading.Thread(target=update_temp, args=())
        t_disp = threading.Thread(target=display_resource_listener, args=())
        
        t_temp.start()
        t_disp.start()
    

if __name__ == "__main__":
    server = CoAPServer("0.0.0.0", 5683, False)
    
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Shutting down..."
        server.close()
        print "Exiting..."
