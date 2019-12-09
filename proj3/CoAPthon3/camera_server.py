#!/usr/bin/python
import sys, os, threading, socket, smtplib, ssl, email, subprocess
import RPi.GPIO as GPIO

from time import sleep
from picamera import PiCamera
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from coapthon.server.coap import CoAP
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource

# 0: RECORD
# 1: STREAM
VIDEO_MODE = 0

PICAM = PiCamera()
PICAM.vflip = True
PICAM.hflip = True
cam_lock = threading.Lock()

def get_LAN_IP():
    gateway = os.popen("ip -4 route show default").read().split()

    ip = ''

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.connect((gateway[2], 0))
        ip = sock.getsockname()[0]

    return ip

class VideoResource(Resource):

    global PICAM

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

        cam_lock.acquire()

        PICAM.resolution = (1920, 1080)
        PICAM.framerate  = 30

        try:
            with socket.socket() as sock:
                IP = get_LAN_IP()
                sock.bind((IP, port))
                print ('Listening for connections on %s:%d' % (IP, port))
                sock.listen()

                conn, addr = sock.accept()
                print ('connected by ', addr)

                conn = conn.makefile('wb')

                PICAM.start_recording(conn, format='h264')

                while self.streaming:
                    PICAM.wait_recording(5)

                PICAM.stop_recording()
        except BrokenPipeError:
            print ('stream terminated')
        finally:
            conn.close()
            cam_lock.release()

# end VideoResource

class SnapshotResource(Resource):

    global PICAM

    TCP_PORT = 44444

    def __init__(self, name='SnapshotResource', coap_server=None):
        super(SnapshotResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = None
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

    def capture_image(self):

        cam_lock.acquire()

        PICAM.resolution = (1024, 768)
        sleep(2)
        PICAM.capture('capture.jpg')

        cam_lock.release()

    # Opens a socket for sending data to the client
    #  The value of mode indicates a snapshot (0) or video stream (1)
    def open_socket(self, port):
        with socket.socket()  as sock:

            IP = get_LAN_IP()
            sock.bind((IP, port))
            print ('Listening for TCP connections on %s:%d' % (IP, port))
            sock.listen()
            conn, addr = sock.accept()
            print ('connected by ', addr)

            self.capture_image()

            with open('capture.jpg', 'rb') as img:
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
    def render_GET(self, request):
        self.payload = str(self.TCP_PORT)
        socket_thread = threading.Thread(target=self.open_socket, args=((self.TCP_PORT,)))
        socket_thread.start()

        return self

# end SnapshotResource

class PIRResource(Resource):
    global PICAM
    PIR = 7
    timeout = 120 # seconds to wait before emailing
    send_mail = True
    capture_index = 0

    def __init__(self, name="PIRResource", coap_server=None):
        super(PIRResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "PIR Resource"
        self.resource_type = "rt1"
        self.content_type = "text/plain"
        self.interface_type = "if1"

        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.PIR, GPIO.IN)
        GPIO.add_event_detect(self.PIR, GPIO.BOTH, callback=self.on_motion)

    def on_motion(self, PIN):

        MAX_CAPTURES = 10

        fname = f'capture{self.capture_index % MAX_CAPTURES}.jpg'
        sender = 'iot433proj3@gmail.com'
        receiver = 'tdmanifo@iu.edu'

        print(f'motion detected {self.capture_index}')
        cam_lock.acquire()

        PICAM.resolution = (1024, 768)
        #PICAM.start_preview()
        #sleep(2)
        PICAM.capture(fname)

        cam_lock.release()

        self.capture_index += 1

        if self.send_mail == True:

            print ('send email')

            self.send_mail = False

            msg = MIMEMultipart()
            msg['From'] = sender
            msg['To'] = receiver
            msg['subject'] = 'Motion detected'

            with open(fname, 'rb') as img:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(img.read())

            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attatchment; filename={fname}',)

            msg.attach(part)
            text = msg.as_string()

            ssl_port = 465
            context = ssl.create_default_context()

            with smtplib.SMTP_SSL('smtp.gmail.com', ssl_port, context=context) as mail:
                mail.login(sender, 'Testing433')
                mail.sendmail(sender, receiver, text)

            wait_thread = threading.Thread(target=self.mail_wait, args=((self.timeout,)))

    def mail_wait(self, timeout):
        sleep(timeout)
        self.send_mail = True

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

        self.add_resource('snapshot', self.snap)
        self.add_resource('video', self.video)
        self.add_resource('PIR', self.pir)

        #self.init_PIR()

        print ('Starting server on %s:%d' % (host, port))
        print (self.root.dump())

# end CoAPServer

if __name__ == "__main__":
    IP = get_LAN_IP()
    #IP = socket.gethostbyname(socket.gethostname())
    PORT = 55555
    server = CoAPServer(IP, PORT, False)

    try:
        server.listen(10)
    except KeyboardInterrupt:
        print ("Shutting down...")
        server.close()
        print ("Exiting...")
