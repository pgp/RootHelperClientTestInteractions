from net_common import *
import struct
import sys


if __name__ == "__main__":
    sock = get_connected_local_socket()

    file_path = encodeString("/sdcard/1.xlsx")
    link_path = encodeString("/sdcard/1.link")

    # rq = b'\x17' # soft link (flags 000)
    rq = bytearray([ord(b'\x17') ^ (2 << 5)]) # hard link (flags 010)

    sock.sendall(rq)
    sock.sendall(struct.pack("=H", len(file_path)))
    sock.sendall(struct.pack("=H", len(link_path)))
    sock.sendall(file_path)
    sock.sendall(link_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
        sys.exit(0)

    sock.close()
