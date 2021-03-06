from __future__ import print_function
import platform
import socket
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
    o = platform.uname()[0].lower()
    if 'linux' in o:
        str1 = "\0" + pathname
    elif 'darwin' not in o and 'win' in o:
        raise OSError("Unsupported local sockets on Windows OS")
    else: # apple and bsd
        str1 = "/tmp/"+pathname
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
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

def pathConcat(base_path, sub_path, sep=None, detectSep=False):
    if detectSep:
        if '/' in base_path:
            return os.path.join(base_path, sub_path).replace('\\', '/')
        elif '\\' in base_path:
            return os.path.join(base_path, sub_path).replace('/', '\\')
    joined_path = os.path.join(base_path, sub_path)
    if sep:
        joined_path = joined_path.replace('\\', sep).replace('/',sep)
    return joined_path