# -*- coding: utf-8 -*-
from time import sleep

from standalone_xre.xre_common import receiveStringWithLen
from net_common import *
import struct
import sys
from datetime import datetime


def loopOverContent(sock):
    cnt = []
    while True:
        ll = struct.unpack("@H", sock.recv(2))[0]  # receive file entry (filename) length
        if ll == 0: break
        fname = sock.recv(ll).decode("utf-8")  # receive file entry (filename)
        fdate = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
        fperms = sock.recv(10).decode("utf-8")
        fsize = struct.unpack("@Q", sock.recv(8))[0]

        cnt.append((fname, fdate, fperms, fsize))
        print(fname + '\t' + str(fdate) + '\t' + fperms + '\t' + str(fsize))
    sock.close()


def listDir(path):
    sock = get_connected_local_socket()
    path = encodeString(path)

    sock.sendall(b'\x01')  # LS request

    sock.sendall(struct.pack("@H", len(path)))  # len of path as unsigned short
    sock.sendall(path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        if resp == b'\x11':
            print('Received redirect on', receiveStringWithLen(sock))
        else:
            print("Error byte received, errno:", struct.unpack("=i", sock.recv(4))[0])
            sys.exit(0)

    loopOverContent(sock)


def listArchive(path):
    sock = get_connected_local_socket()
    path = encodeString(path)

    # flags = 7 # standard list archive
    flags = 6 # for checking whether the archive contains one or more items at the top level

    rq = bytearray([ord(b'\x01') ^ (flags << 5)])  # LS archive request
    sock.sendall(rq)

    sock.sendall(struct.pack("@H", len(path)))  # len of path as unsigned short
    sock.sendall(path)

    # send empty password
    sock.sendall(b'\x00')
    # or send non-empty password
    # pwd = encodeString("qwerty")
    # sock.sendall(struct.pack("@B",len(pwd)))
    # sock.sendall(pwd)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        if resp == b'\x11':
            print('Protocol error - Redirect response not allowed in list archive', receiveStringWithLen(sock))
        else:
            print("Error byte received, errno:", struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)

    if flags == 7:
        loopOverContent(sock)
    else: # flags == 6
        retval = struct.unpack("=Q", sock.recv(8))[0]
        if retval == 2:
            print("The archive contains more than one item at the top level")
        elif retval == 1:
            print("The archive contains only one item at the top level")
        else:
            print("There were undetected errors during archive listing")


if __name__ == "__main__":
    listDir('')
    # listDir('/')
    print('sleeping')
    sleep(2)
    listArchive('/sdcard/1.7z')
