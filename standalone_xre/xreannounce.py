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
import traceback
from binascii import crc32
try:
    from SocketServer import *
except ImportError:
    from socketserver import *
try:
    unicode = unicode # only on Python 2
except:
    unicode = None

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
server.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
# Set a timeout so the socket does not block
# indefinitely when trying to receive data.
server.settimeout(0.2)
server.bind(("", 44444))

host = bytes("192.168.12.34","utf-8")
path = bytes("/sdcard","utf-8")
port = 11111

message = struct.pack("@H", port) + struct.pack("@H", len(host)) + host + struct.pack("@H", len(path)) + path
msgcrc = struct.pack("@I", binascii.crc32(message))

while True:
    server.sendto(msgcrc + message, ('192.168.43.255', 11111))
    print("message sent!")
    time.sleep(2)
