from __future__ import print_function
import socket, ssl, pprint
from time import sleep

"""
TLS client example, using python's native openssl bindings.
Should work on both python 2 and 3, and both openssl 1.0 and 1.1
"""

if __name__ == '__main__':
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Require a certificate from the server. We used a self-signed certificate
    # so here ca_certs must be the server certificate itself.
    tls_sock = ssl.wrap_socket(s,
                               ca_certs="dummycrt.pem",
                               cert_reqs=ssl.CERT_REQUIRED)

    tls_sock.connect(('localhost', 11111))

    print(repr(tls_sock.getpeername()))
    print(tls_sock.cipher())
    print(pprint.pformat(tls_sock.getpeercert()))

    # logic for communicating with simple TLS echo server (not implemented here)
    # i=0
    # while True:
    #     tls_sock.write(("cnt is "+str(i)).encode('utf-8'))
    #     print("Received response:\n", tls_sock.recv(1024).decode('utf-8'))
    #     i+=1
    #     sleep(1)
