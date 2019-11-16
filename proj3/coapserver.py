#!/usr/bin/python
import sys
import os
import threading
import Adafruit_DHT
import RPi.GPIO as GPIO
from RPLCD.gpio import CharLCD
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
    humidity_resource = BasicResource()
    
    lcd = CharLCD(cols=16, rows=2, pin_rs=37, pin_e=35, pins_data=[33, 31, 29, 23], numbering_mode=GPIO.BOARD)
    
    lock = threading.Lock()

    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        self.add_resource('temperature/', self.temperature_resource)
        self.add_resource('display/', self.display_resource)
        self.add_resource('humidity/', self.humidity_resource)
        
        # use display 1 as default
        self.display_resource.payload = '1'
        
        print "CoAP Server start on " + host + ":" + str(port)
        print self.root.dump()

        self.lcd.clear()
    
        t_stats = threading.Thread(target=self.get_temp_humidity, args=())
        t_lcd = threading.Thread(target=self.display_resource_listener, args=())
        t_stats.start()
        t_lcd.start()
        
    def get_temp_humidity(self):
        
        while True:
            
            h, t = Adafruit_DHT.read_retry(11, 4)
            
            self.humidity_resource.payload = str(h)
            self.temperature_resource.payload = str(t)
            
            #self.lcd.cursor_pos = (0,0)
            #self.lcd.write_string("T: %d C " % t)
            #self.lcd.cursor_pos = (1,0)
            #self.lcd.write_string("H: %d %%" % h)
            
            sleep (1)
        

    # runs on a thread and periodically checks the value on 'display/' resource
    # sets the corresponding display based on the payload value
    def display_resource_listener(self):
 
        while True:
            self.lcd.clear()
            self.lcd.cursor_pos = (0,0)
        
            # toggle to display 1
            if self.display_resource.payload == '1':
                self.lcd.write_string("T: %s C " % self.temperature_resource.payload)
            # toggle to display 2
            elif self.display_resource.payload == '2':
                self.lcd.write_string("H: %s %%" % self.humidity_resource.payload)
            
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
