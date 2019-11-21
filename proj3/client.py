
import sys
import socket
from coapthon.client.helperclient import HelperClient
from coapthon.utils import parse_uri

#HOST = input ("enter host: ")
HOST = socket.gethostbyname(socket.gethostname())
COAP_PORT = 55555
TCP_PORT  = 44444

try:
    # ask CoAP server for camera resource
    client = HelperClient(server=(socket.gethostbyname('Spectre'), COAP_PORT))
    response = client.get('/camera')
    print(response.pretty_print())

    # check what port the server is openeing for communication
    if (server_port := int(response.payload)) is not None:
        server_ip = response.source[0]

        # attempt to establish comms with the server
        with socket.socket() as sock:
            sock.connect((server_ip, server_port))
            print ('connected to %s:%d' % (server_ip, server_port))
            # download the file
            with open('recv.png', 'wb') as img:
                r = 0
                while True:
                    data = sock.recv(1024)
                    if not data:
                        break
                    r += len(data)
                    sys.stdout.write ('Received %d KB          \r' % (r/1000))
                    sys.stdout.flush()
                    img.write(data)
                sys.stdout.write('\n')


    # accept incoming socket connections
    # if response:
    #     # establish the TCP server socket
    #     with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    #         sock.bind((HOST, TCP_PORT))
    #         sock.listen()
    #         print('Listening for TCP comms on %s:%d ' % (HOST, TCP_PORT))
    #         connection, address = sock.accept()
    #         print ('connected by %s' % address)
    #         with open('recv.png','wb') as img:
    #             while True:
    #                 data = connection.recv(1024)
    #                 if not data:
    #                     break
    #                 print ('Received %d KB' % len(data))
    #                 img.write(data)
    #
    #         connection.close()

    # with open('recv.png', 'wb') as img:
    #     while True:
    #         data = sock.recv(1024)
    #         if not data:
    #             break
    #         img.write(data)
except KeyboardInterrupt:
    connection.close()

client.stop()
#print('Received: ', repr(data), ' | ', data.decode())
