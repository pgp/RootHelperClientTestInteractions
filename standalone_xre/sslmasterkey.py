import ctypes
import platform

platform_name = platform.uname()[0].lower()

"""
Web source:
https://github.com/joernheissler/SslMasterKey
"""

library_names = {
    'linux': 'libssl.so.1.1',
    'darwin': 'libssl.1.1.dylib',
    'freebsd': '/usr/local/lib/python3.7/lib-dynload/_ssl.so', # or use export LD_LIBRARY_PATH and provide only filename _ssl.so
    'windows': 'libssl-1_1-x64.dll'
}

libssl = ctypes.cdll.LoadLibrary(library_names[platform_name]) # works only on Python 3 with openssl 1.1

# size_t SSL_SESSION_get_master_key(const SSL_SESSION *session, unsigned char *out, size_t outlen);
SSL_SESSION_get_master_key = libssl.SSL_SESSION_get_master_key
SSL_SESSION_get_master_key.restype = ctypes.c_size_t
SSL_SESSION_get_master_key.argtypes = ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t

# size_t SSL_get_client_random(const SSL *ssl, unsigned char *out, size_t outlen);
SSL_get_client_random = libssl.SSL_get_client_random
SSL_get_client_random.restype = ctypes.c_size_t
SSL_get_client_random.argtypes = ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t


class PyObject(ctypes.Structure):
    _fields_ = [
        ('ob_refcnt', ctypes.c_size_t),
        ('ob_type', ctypes.c_void_p),
    ]


class PySSLSocket(ctypes.Structure):
    _fields_ = [
        ('head', PyObject),
        ('Socket', ctypes.c_void_p),
        ('ssl', ctypes.c_void_p),
    ]


class PySSLSession(ctypes.Structure):
    _fields_ = [
        ('head', PyObject),
        ('session', ctypes.c_void_p),
    ]


def get_ssl_master_key(sock):
    """
    sock: ssl.SSLSocket
    """

    # Modules/_ssl.c, PySSLSocket
    sslconn = sock._sslobj._sslobj if platform_name == 'linux' else sock._sslobj
    ssl_ptr = PySSLSocket.from_address(id(sslconn)).ssl

    # Call SSL_get_client_random with a buffer and format result
    buf = ctypes.create_string_buffer(4096)
    res = SSL_get_client_random(ssl_ptr, buf, len(buf))
    # client_random = bytes(buf)[:res].hex() # only working on Python 3, hex() method not present in Python 2

    # Modules/_ssl.c, PySSLSession
    session = sslconn.session # not working on Python 2!
    session_ptr = PySSLSession.from_address(id(session)).session

    # Call SSL_SESSION_get_master_key with a buffer and format result
    buf = ctypes.create_string_buffer(4096)
    res = SSL_SESSION_get_master_key(session_ptr, buf, len(buf))
    # master_key = bytes(buf)[:res].hex()
    # return ' '.join(['CLIENT_RANDOM', client_random, master_key])
    master_key = bytearray(bytes(buf)[:res])
    return master_key
