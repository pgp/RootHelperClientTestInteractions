from net_common import *
import struct

if __name__ == "__main__":
    sock = get_connected_local_socket()

    rq = b'\x0E'
    socket_name = encodeString("anotherroothelper")

    sock.sendall(rq)
    sock.sendall(struct.pack("=H", len(socket_name)))  # len of path as unsigned short
    sock.sendall(socket_name)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
    else:
        print("OK response received")
    sock.close()
