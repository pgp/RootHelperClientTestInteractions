from net_common import *
from datetime import datetime
import struct


def stats_file(path):
    sock = get_connected_local_socket()

    #  send stat request
    # rq = chr(ord('\x05') ^ (1 << 5))  # file stats (flag bits: 001_2 = 1) # only Python 2
    rq = bytearray([ord(b'\x05') ^ (1 << 5)])  # file stats (flag bits: 001_2 = 1)

    sock.sendall(rq)
    bpath = encodeString(path)
    sock.sendall(struct.pack("@H", len(bpath)))  # len of path as unsigned short
    sock.sendall(bpath)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received")
        print("errno:", struct.unpack("@I", sock.recv(4))[0])
        sock.close()
        return
    else:
        print("OK response received")

    groupLen = struct.unpack("@B", sock.recv(1))[0]
    group = sock.recv(groupLen)
    print("Group:", group)
    ownerLen = struct.unpack("@B", sock.recv(1))[0]
    owner = sock.recv(ownerLen)
    print("Owner:", owner)
    creationTime = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
    lastAccessTime = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
    modificationTime = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
    print("File times:", creationTime, lastAccessTime, modificationTime)
    permissions = sock.recv(10).decode('utf-8')
    print("Permissions:", permissions)
    size = struct.unpack("@Q", sock.recv(8))[0]
    print("Size:", size)

    sock.close()


def stats_dir(path):
    sock = get_connected_local_socket()

    #  send stat request
    # rq = chr(ord('\x05') ^ (2 << 5))  # dir stats (flag bits: 010_2 = 2)
    rq = bytearray([ord(b'\x05') ^ (2 << 5)])  # dir stats (flag bits: 010_2 = 2)

    sock.sendall(rq)
    bpath = encodeString(path)
    sock.sendall(struct.pack("@H", len(bpath)))  # len of path as unsigned short
    sock.sendall(bpath)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received")
        print("errno:", struct.unpack("@I", sock.recv(4))[0])
    else:
        print("OK response received")

    childrenDirs = struct.unpack("@Q", sock.recv(8))[0]
    print("children dirs:", childrenDirs)
    childrenFiles = struct.unpack("@Q", sock.recv(8))[0]
    print("children files:", childrenFiles)
    totalDirs = struct.unpack("@Q", sock.recv(8))[0]
    print("total dirs:", totalDirs)
    totalFiles = struct.unpack("@Q", sock.recv(8))[0]
    print("total files:", totalFiles)
    totalSize = struct.unpack("@Q", sock.recv(8))[0]
    print("total size:", totalSize)

    sock.close()

def stats_multiple(paths):
    sock = get_connected_local_socket()

    #  send stat request
    # rq = chr(ord('\x05') ^ (4 << 5))  # multiple items stats (flag bits: 100_2 = 4)
    rq = bytearray([ord(b'\x05') ^ (4 << 5)])  # multiple items stats (flag bits: 100_2 = 4)

    sock.sendall(rq)
    for path in paths:
        bpath = encodeString(path)
        sock.sendall(struct.pack("@H", len(bpath)))  # len of path as unsigned short
        sock.sendall(bpath)
    sock.sendall(bytearray([0,0])) # end-of-list indication

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received")
        print("errno:", struct.unpack("@I", sock.recv(4))[0])
    else:
        print("OK response received")

    childrenDirs = struct.unpack("@Q", sock.recv(8))[0]
    print("children dirs:", childrenDirs)
    childrenFiles = struct.unpack("@Q", sock.recv(8))[0]
    print("children files:", childrenFiles)
    totalDirs = struct.unpack("@Q", sock.recv(8))[0]
    print("total dirs:", totalDirs)
    totalFiles = struct.unpack("@Q", sock.recv(8))[0]
    print("total files:", totalFiles)
    totalSize = struct.unpack("@Q", sock.recv(8))[0]
    print("total size:", totalSize)

    sock.close()

if __name__ == "__main__":

    # stats_file('/sdcard/2.bin')
    # stats_dir('/sdcard/a\nb')
    stats_multiple(['/sdcard/a\nb','/sdcard/2.bin','/sdcard/3.bin'])
