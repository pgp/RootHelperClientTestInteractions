from __future__ import print_function
from xre_common import *
from sslmasterkey import get_ssl_master_key

"""
This is a python implementation of the XFiles Remote Explorer (XRE) server-side protocol.
The TLS channel is established using python's openssl native bindings.
The TLS session master secret for end-to-end verification is extracted by looking up in the native C structures
(see sslmasterkey.py; with this feature enabled, it works on any well known OS - Windows,OSX,Linux,BSD - with Python 3 and OpenSSL 1.1 bindings;
commenting the relevant code lines should make it work also with Pyhton 2.7, and with OpenSSL 1.0 bindings)
"""

def xre_server_session_wrapper(conn):
    client_host, client_port = conn.getpeername()
    print("Serving client:", client_host, " at port:", client_port)
    print("Ciphersuite:", conn.cipher())

    from hashlib import sha256
    sha_ = sha256(get_ssl_master_key(conn))
    print("SHA256 of this session's master secret:\n", sha_.hexdigest())
    xre_server_session(conn)


if __name__ == '__main__':
    bindsocket = socket.socket()
    bindsocket.bind(('', 11111))
    bindsocket.listen(5)
    print('XRE server started')
    while True:
        newsocket, fromaddr = bindsocket.accept()
        connstream = ssl.wrap_socket(newsocket,
                                     server_side=True,
                                     ssl_version=ssl.PROTOCOL_TLSv1_2,
                                     certfile="dummycrt.pem",
                                     keyfile="dummykey.pem")
        t = threading.Thread(target=xre_server_session_wrapper, args=(connstream,))
        t.setDaemon(True)
        t.start()
