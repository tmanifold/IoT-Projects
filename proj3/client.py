
import sys, socket
# import cv2
import coapthon
from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri
from datetime import datetime

#HOST = input ("enter host: ")
HOST = socket.gethostbyname(socket.gethostname())
COAP_PORT = 55555
TCP_PORT  = 44444

try:
    IP = input ("Enter server hostname/IP: ")
    res = input ('Enter requested resource: ')
    res_path = '/' + res
    print ('requesting ', res_path)
    # ask CoAP server for camera resource
    client = HelperClient(server=(IP, COAP_PORT))
    method = input ('1. GET\n2. OBSERVE\n> ')
    if method == '1':
        response = client.get(res_path)
    elif method == '2':
       response = client.observe(res_path)
    print(response.pretty_print())

    # check what port the server is openeing for communication
    if (server_port := int(response.payload)) is not None:
    #if response.payload is not None:
    #    server_port = int(response.payload)
        server_ip = response.source[0]
        # attempt to establish comms with the server
        with socket.socket() as sock:
            sock.connect((server_ip, server_port))
            print ('connected to %s:%d' % (server_ip, server_port))

            if method == '1':
                with open('recv.png', 'wb') as img:
                    r = 0
                    while True:
                        data = sock.recv(4096)
                        if not data:
                            break
                        r += len(data)
                        sys.stdout.write('received %d B         \r' % (r))
                        sys.stdout.flush()
                        img.write(data)
                    sys.stdout.write('\n')

        client.stop()
        print ('socket closed')

except KeyboardInterrupt:
    client.stop()
#print('Received: ', repr(data), ' | ', data.decode())
