#!/usr/bin/python
import sys, os, threading, socket, cv2
from PyQt5.QtMultimedia import QCamera, QCameraInfo, QCameraImageCapture, QMediaRecorder

## Reference QCamera or cv2 for video/image capture ##

import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource

class CameraResource(Resource):

    TCP_PORT = 44444
    img_path = 'monkaS.png'
    streaming = False

    def __init__(self, name="CameraResource", coap_server=None):
        super(CameraResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)

        self.payload = None
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"



    # Opens a socket for sending data to the client
    #  The value of mode indicates a snapshot (0) or video stream (1)
    def open_socket(self, mode=0):
        with socket.socket()  as sock:
            IP = socket.gethostbyname(socket.gethostname())
            sock.bind((IP, self.TCP_PORT))
            print ('Listening for TCP connections on %s:%d' % (IP, self.TCP_PORT))
            sock.listen()
            conn, addr = sock.accept()
            print ('connected by ', addr)

            cam = cv2.VideoCapture(0)

            if mode == 0:
                ret, frame = cam.read()
                #r, frame = cv2.imencode('.jpg', frame, enc)

                cv2.imwrite('capture.png', frame)

                print ('size of frame: %d B' % len(bytearray(frame)))

                with open('capture.png', 'rb') as img:
                    data = img.read(4096)
                    r = len(data)
                    while (data):
                        conn.send(data)
                        r += len(data)
                        data = img.read(4096)
                        sys.stdout.write('Sent %d B          \r' % (r))
                        sys.stdout.flush()

            elif mode == 1:
                    pass

            conn.close()

    # When a CoAP GET request is received, this method will ACK with a port number
    #  on which a socket will be opened for the requesting client.
    # TODO:
    #   Assign a unique port number for each client
    def render_GET(self, request):
        self.payload = str(self.TCP_PORT)

        socket_thread = threading.Thread(target=self.open_socket, args=())
        socket_thread.start()

        return self

    def render_OBSERVE(self, request):

        if self.streaming == False:
            self.payload = str(self.TCP_PORT)
            self.streaming = True

            socket_thread = threading.Thread(target=self.open_socket, args=(1))
            socket_thread.start()

        return self

# end CameraResource

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
