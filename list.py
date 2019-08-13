# -*- coding: utf-8 -*-
from net_common import *
import struct
import sys
from datetime import datetime

if __name__ == "__main__":
    sock = get_connected_local_socket()

    # rootpath = encodeString("/")
    rootpath = encodeString("/sdcard/1.7z")

    # sock.sendall(b'\x01')  # LS request
    rq = bytearray([ord(b'\x01') ^ (1 << 5)])  # LS archive request
    sock.sendall(rq)

    sock.sendall(struct.pack("@H", len(rootpath)))  # len of path as unsigned short
    sock.sendall(rootpath)

    # send empty password
    sock.sendall(b'\x00')
    # or send non-empty password
    # pwd = encodeString("qwerty")
    # sock.sendall(struct.pack("@B",len(pwd)))
    # sock.sendall(pwd)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)
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
