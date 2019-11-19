#!/usr/bin/python
import sys
import os
import threading

import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from coapthon.resources.resource import Resource

class CameraResource(Resource):

    img_path = './monkaS.png'

    def __init__(self, name="CameraResource", coap_server=None):
        super(CameraResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        # max payload size will have to be ~65.5KB if sending image data as plain-text
        self.payload = self.get_image()
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    def get_image(self):
        with open(self.img_path, "rb") as image:
            ba = bytearray(image.read())
            return ba

    def render_GET(self, request):
        self.payload = self.get_image()
        return self

class PIRResource(Resource):
    def __init__(self, name="PIRResource", coap_server=None):
        super(PIRResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "PIR Resource"
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    def render_GET(self, request):
        return self
#end PIR

class CoAPServer(CoAP):

    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        self.add_resource('camera/', CameraResource())
        self.add_resource('PIR/', PIRResource())

        print self.root.dump()


# end CoAPServer

if __name__ == "__main__":
    server = CoAPServer("0.0.0.0", 5683, False)

    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Shutting down..."
        server.close()
        print "Exiting..."
