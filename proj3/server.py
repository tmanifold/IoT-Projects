#!/usr/bin/python
import sys, os, threading, socket, cv2
from picamera import PiCamera
#from PyQt5.QtMultimedia import QCamera, QCameraInfo, QCameraImageCapture, QMediaRecorder

## Reference QCamera or cv2 for video/image capture ##

import RPi.GPIO as GPIO
from time import sleep
from coapthon.server.coap import CoAP
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource

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

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            IP = socket.gethostbyname(socket.gethostname())
            sock.bind((IP, port))
            print ('Listening for connections on %s:%d' % (IP, port))
            sock.listen()

            conn, addr = sock.accept()
            print ('connected by ', addr)

            cam = cv2.VideoCapture(0)

            while self.streaming:
                ret, frame = cam.read()
                data = cv2.imencode('.png', frame)[1].tostring()
                sock.sendall(data)
# end VideoResource

class SnapshotResource(Resource):

    TCP_PORT = 44444

    def __init__(self, name='SnapshotResource', coap_server=None):
        super(SnapshotResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = None
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    def capture_image(self):
        camp = cv2.VideoCapture(0)
        ret, frame = cam.read()

        cv2.imwrite('capture.png', frame)

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

        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.PIN, GPIO.IN)
        GPIO.add_event_detect(self.PIN, GPIO.RISING, callback=self.on_montion)

    def on_motion(self):
        # capture single image
        cam = PiCamera()

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
