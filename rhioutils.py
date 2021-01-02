from __future__ import print_function
import sys
import os
import os.path
import socket
import time
import getopt
import binascii
import ssl
import struct
import threading
import locale
import re
import traceback
try:
    from SocketServer import *
except ImportError:
    from socketserver import *
try:
    unicode = unicode # only on Python 2
except:
    unicode = None

def killProcess(pid):
    if os.name == 'nt':
        import ctypes
        PROCESS_TERMINATE = 1
        handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, pid)
        ctypes.windll.kernel32.TerminateProcess(handle, -1)
        ctypes.windll.kernel32.CloseHandle(handle)
    else:
        import signal
        os.kill(pid, signal.SIGINT)


def exitWithError(error):
    print(error)
    killProcess(os.getpid())


def createRandomFile(filename, n):
    with open(filename, 'wb') as f:
        f.write(os.urandom(n))


# file f must be open in binary mode: f = open(filename,'rb')
def readAll(f, count):
    try:
        total = b''
        remaining = count
        while True:
            chunk = f.read(remaining)
            if not chunk: return chunk
            total += chunk
            remaining -= len(chunk)
            if remaining == 0:
                return total
    except:
        print('Error in std file read')
        traceback.print_exc()
        return b''


def readAllOrExit(fd, count):
    total = readAll(fd, count)
    if len(total) < count:
        print('Incomplete read, exiting')
        sys.exit(-234)
    return total


def standardizeToXrePath(s_):
    if '/' in s_: # already in POSIX format, nothing to do
        return s_
    else: # possibly a windows path, try to convert it
        return windowsToUnixPath(s_, unconditional=True)


def standardizeFromXrePath(s_):
    if not isinstance(s_, str):
        s_ = s_.decode('utf-8')
    p = re.compile(r"^/[a-zA-Z]:")
    if p.match(s_) is None:
        return s_
    else:
        return unixToWindowsPath(s_, unconditional=True)


def windowsToUnixPath(s_, unconditional=False):
    """
    :param s_: string to encode or already encoded bytes for python 2,
               only string type for python 3, in order to perform path separator replacement
    :param unconditional: when True, the conversion will be performed ignoring the host OS
           (i.e. on a Unix OS, providing a Windows path will result in it being converted)
    :return: bytes to be sent over socket (can be str passthrough for python 2)
    """
    if unicode is not None: # python 2
        if type(s_) is unicode:
            s = s_.encode('utf-8')
        # type mapping: in python 2, str is bytes!
        elif type(s_) is str: # aka bytes (after encoding, expected already UTF-8)
            s = s_
        else:
            exitWithError("Invalid string format in windowsToUnixPathEncoded, input type is "+str(type(s_)))
            return
        return '/' + s.replace('\\', '/') if unconditional or os.name == 'nt' else s
    else: # python 3, expect path in str format
        if type(s_) is str:
            s = s_
            ret = '/' + s.replace('\\', '/') if unconditional or os.name == 'nt' else s
            return ret.encode('utf-8')
        else:
            exitWithError("Invalid string format in windowsToUnixPathEncoded, input type is "+str(type(s_)))


def unixToWindowsPath(s_, unconditional=False):
    s = s_.decode('utf-8') if type(s_) is bytes or type(s_) is bytearray else s_
    if os.name != 'nt' and not unconditional: return s
    if s[0] != '/':
        exitWithError('Mannaggia')  # sys.exit is not enough, we are multithreaded
        return
    x = s[1:].replace('/', '\\')
    if x == 'c:' or x == 'C:':
        x = 'c:\\'  # os.listdir('c:') will actually list current directory!!!
    return x
