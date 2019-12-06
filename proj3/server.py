#!/usr/bin/python
import sys, os, threading, socket, subprocess
# import cv2
from picamera import PiCamera

import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource

# 0: RECORD
# 1: STREAM
VIDEO_MODE = 0

class VideoResource(Resource):
    TCP_PORT = 44444
    streaming = False

    def __init__(self, name='VideoResource', coap_server=None):
        super(VideoResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = None
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    def render_GET(self, request):
        self.payload = str(self.TCP_PORT)

        if self.streaming == False:
            self.payload = str(self.TCP_PORT)
            self.streaming = True

            socket_thread = threading.Thread(target=self.open_socket, args=((self.TCP_PORT,)))
            socket_thread.start()
        else:
            self.streaming == False

        return self

    def open_socket(self, port):
        picam = PiCamera()
        picam.resolution = (1920, 1080)
        picam.framerate  = 10
        
        with socket.socket() as sock:
            IP = socket.gethostbyname(socket.gethostname())
            sock.bind((IP, port))
            print ('Listening for connections on %s:%d' % (IP, port))
            sock.listen()

            conn, addr = sock.accept()
            print ('connected by ', addr)
            
            conn.makefile('wb')
            
            picam.start_recording(conn, format='h264')
            
            while self.streaming:
                picam.wait_recording(5)
            
            picam.stop_recording()
            conn.close()
            
# end VideoResource

class SnapshotResource(Resource):

    TCP_PORT = 44444
    camera = None
	
    def __init__(self, name='SnapshotResource', coap_server=None):
        super(SnapshotResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = None
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    def capture_image(self):
        #camp = cv2.VideoCapture(0)
        #ret, frame = cam.read()

        #cv2.imwrite('capture.png', frame)
        camera = PiCamera()
        camera.resolution = (1024, 768)
        camera.startpreview()
        sleep(2)
        camera.capture('capture.jpg')

    # Opens a socket for sending data to the client
    #  The value of mode indicates a snapshot (0) or video stream (1)
    def open_socket(self, port):
        with socket.socket()  as sock:
            IP = socket.gethostbyname(socket.gethostname())
            sock.bind((IP, port))
            print ('Listening for TCP connections on %s:%d' % (IP, port))
            sock.listen()
            conn, addr = sock.accept()
            print ('connected by ', addr)

            self.capture_image()

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


            conn.close()

    # When a CoAP GET request is received, this method will ACK with a port number
    #  on which a socket will be opened for the requesting client.
    # TODO:
    #   Assign a unique port number for each client
    def render_GET(self, request):
        self.payload = str(self.TCP_PORT)

        socket_thread = threading.Thread(target=self.open_socket, args=((self.TCP_PORT,)))
        socket_thread.start()

        return self

# end SnapshotResource

class PIRResource(Resource):

    PIN = 7

    def __init__(self, name="PIRResource", coap_server=None):
        super(PIRResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "PIR Resource"
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIN, GPIO.IN)
        
        GPIO.add_event_detect(self.PIN, GPIO.RISING, callback=self.on_motion)

    def on_motion(self, PIN):
        # capture single image
        cam = PiCamera()
        print ('motion detected')

    def render_GET(self, request):
        return self

    def render_OBSERVE(self, request):
        return self
# end PIR

class CoAPServer(CoAP):

    #PIR = 7
    snap  = SnapshotResource()
    video = VideoResource()
    pir   = PIRResource()

    def __init__(self, host, port, multicast=False):
        CoAP.__init__(self, (host, port), multicast)

        self.add_resource('snapshot/', self.snap)
        self.add_resource('video/', self.video)
        self.add_resource('PIR/', self.pir)

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
