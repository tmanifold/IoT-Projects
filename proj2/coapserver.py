#!/usr/bin/python

#import sys
import os
import threading
import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from exampleresources import BasicResource

# load the necessary kernel modules for using the temperature sensor
os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')

class CoAPServer(CoAP):

    # resources to be added to the server. These will be monitored or
    #  updated by threads.
    # temperature is read from the device file and written to the
    #  'temperature/' resource payload
    # use PUT to update 'display/' resource via Copper
    temperature_resource = BasicResource()
    display_resource = BasicResource()

    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        self.add_resource('temperature/', self.temperature_resource)
        self.add_resource('display/', self.display_resource)
        
        # use display 1 as default
        self.display_resource.payload = '1'
        
        print "CoAP Server start on " + host + ":" + str(port)
        print self.root.dump()

        t_temp = threading.Thread(target=self.update_temp, args=())
        t_disp = threading.Thread(target=self.display_resource_listener, args=())
        
        t_temp.start()
        t_disp.start()

    # parse the temperature sensor device file
    # returns the temperaturein celsius as a float
    def get_temp(self):
        f = open('/sys/bus/w1/devices/28-000007550451/w1_slave')
        lines = f.readlines()
        f.close()
        t_pos = lines[1].find("t=")
        return float(lines[1][t_pos+2:t_pos+6]) / 100

    # read the temperature sensor using get_temp() and update the 'temperature/'
    #  resource payload accordingly
    def update_temp(self):

        while True:
            self.temperature_resource.payload = str(self.get_temp())
            sleep(2)

    # runs on a thread and periodically checks the value on 'display/' resource
    # sets the corresponding display based on the payload value
    def display_resource_listener(self):
        
        last_display = 2 # init to 2 so toggle flag works

        while True:
            # toggle to display 1
            if self.display_resource.payload == '1' and last_display == 2:
                print "Display 1"
                last_display = 1
            # toggle to display 2
            elif self.display_resource.payload == '2' and last_display == 1:
                print "Display 2"
                last_display = 2
            
            sleep(1)

# end CoAPServer

if __name__ == "__main__":
    server = CoAPServer("0.0.0.0", 5683, False)
    
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Shutting down..."
        server.close()
        print "Exiting..."
