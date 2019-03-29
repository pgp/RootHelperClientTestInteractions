from net_common import *
import struct
import sys


if __name__ == "__main__":
    sock = get_connected_local_socket()

    file_path = encodeString("/sdcard")

    #  send exists request for created file
    rq = bytearray([ord(b'\x08') ^ (7 << 5)]) # 7 = 111 radix 2 (all flags set)
    # rq = bytearray([ord(b'\x08') ^ (1 << 5)]) # exists
    # rq = bytearray([ord(b'\x08') ^ (3 << 5)]) # is file
    # rq = bytearray([ord(b'\x08') ^ (5 << 5)]) # is dir

    sock.sendall(rq)  # EXIST/ISFILE/ISDIR request
    sock.sendall(struct.pack("=H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received")
        sys.exit(0)

    flags = sock.recv(1)
    print("flags as int:", ord(flags))

    sock.close()

