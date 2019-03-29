from net_common import *
import struct
import sys
import hashlib

if __name__ == '__main__':
    sock = get_connected_local_socket()

    rq = bytearray([ord(b'\x0F') ^ (7 << 5)])  # flags: 111 (fileIO read mode)

    file_path = encodeString('/sdcard/2.bin')
    sock.sendall(rq)  # FILEIO request
    sock.sendall(struct.pack("=H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:", struct.unpack("=i", sock.recv(4)))
        sys.exit(0)

    hasher = hashlib.sha512()
    while True:
        s = sock.recv(1024)
        if not s: break
        hasher.update(s)
    print(hasher.hexdigest())
