from __future__ import print_function
from socket import *
import errno
import os

def get_input():
    try:
        return raw_input()
    except NameError:
        return input()

def set_bit(v, index, x):
    """
    Set the index:th bit of v to x, and return the new value.
    Note that bit numbers (index) are from 0, with 0 being the least significant bit.
    """
    mask = 1 << index
    v &= ~mask
    if x:
        v |= mask
    return v

def encodeString(s):
    return bytearray(s.encode('utf-8'))

def get_connected_local_socket(pathname="theroothelper"):
    o = os.uname()[0].lower()
    if 'linux' in o:
        str1 = "\0" + pathname
    elif 'darwin' not in o and 'win' in o:
        raise OSError("Unsupported local sockets on Windows OS")
    else: # apple and bsd
        str1 = "/tmp/"+pathname
    sock = socket(AF_UNIX, SOCK_STREAM)
    sock.connect(str1)
    return sock

def toHex(s_):
    if isinstance(s_,str): # str/bytes in Python 2, unicode string in python 3
        return ":".join("{:02x}".format(ord(c)) for c in s_)
    else:
        if isinstance(s_, bytes) or isinstance(s_, bytearray):
            s = s_ if isinstance(s_,bytearray) else bytearray(s_)
            return ':'.join(format(x, '02x') for x in s)
        else: # try with unicode type, python2 only
            return ":".join("{:02x}".format(ord(c)) for c in s_.encode('utf-8'))

def intFromOctalString(s):
    if s[:2] == '0o': # python 3 syntax
        s = '0'+s[2:] # python 2 syntax
    return int(s, 8)