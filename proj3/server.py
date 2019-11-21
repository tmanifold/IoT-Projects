#!/usr/bin/python
import sys
import os
import threading
import socket

import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource

class CameraResource(Resource):

    TCP_PORT = 44444
    img_path = 'monkaS.png'
    t_sender = threading.Thread()

    def __init__(self, name="CameraResource", coap_server=None):
        super(CameraResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        # max payload size will have to be ~65.5KB if sending image data as plain-text
        self.payload = None
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    # Opens a socket for sending data to the client
    def open_socket(self):
        with socket.socket()  as sock:
            IP = socket.gethostbyname(socket.gethostname())
            sock.bind((IP, self.TCP_PORT))
            print ('Listening for TCP connections on %s:%d' % (IP, self.TCP_PORT))
            sock.listen()
            conn, addr = sock.accept()
            print ('connected by ', addr)

            with open(self.img_path, 'rb') as img:
                data = img.read(1024)
                while (data):
                    conn.send(data)
                    data = img.read(1024)

            conn.close()

    # send an image capture to the host specified by ip:port, wait for delay seconds
    # def send_image(self, DEST_HOST, DEST_PORT, delay=1):
    #     # wait for delay in seconds before sending data
    #     sleep(delay)
    #     try:
    #         sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         # establish the TCP connection to the requester
    #         print ('Establishing TCP connection to %s:%d...' % (DEST_HOST, self.TCP_PORT))
    #         sock.connect((DEST_HOST,self.TCP_PORT))
    #         print ('TCP connection established')
    #
    #         # open the image and begin sending to the requester
    #         with open(self.img_path, 'rb') as img:
    #             print ('sending data...')
    #             data = img.read(1024)
    #             while (data):
    #                 sock.send(data)
    #                 data = img.read(1024)
    #                 print ('\tsent %d bytes' % len(data))
    #
    #     except socket.gaierror:
    #         print('unable to establish TCP connection following GET request')
    #     except socket.timeout:
    #         print ('TCP connection timed out')
    #     finally:
    #         sock.close()

    # When a CoAP GET request is received, this method will ACK with a port number
    #  on which a socket will be opened for the requesting client.
    # TODO:
    #   Assign a unique port number for each client
    #   ACK with filename and file size in addition to port number
    def render_GET(self, request):
        self.payload = str(self.TCP_PORT)

        socket_thread = threading.Thread(target=self.open_socket, args=())
        socket_thread.start()

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

        print ('Starting server on %s:%d' % (host, port))
        print (self.root.dump())


# end CoAPServer

if __name__ == "__main__":
    #IP = '127.0.0.1'
    IP = socket.gethostbyname(socket.gethostname())
    PORT = 55555
    server = CoAPServer(IP, PORT, False)

    try:
        server.listen(10)
    except KeyboardInterrupt:
        print ("Shutting down...")
        server.close()
        print ("Exiting...")
