from net_common import *
import struct
import sys

"""
RSA PKCS8 & X509 PEM key generation
"""
def send_ssh_keygen_rsa_rq(sock):
    rq = bytearray([ord(b'\x16') ^ (0 << 5)])

    # key_size = 2048
    key_size = 4096
    # key_size = 8192

    sock.sendall(rq)
    sock.sendall(struct.pack("@I", key_size))

"""
ed25519 (OpenSSH format) key generation
"""
def send_ssh_keygen_ed25519_rq(sock):
    rq = bytearray([ord(b'\x16') ^ (1 << 5)])
    sock.sendall(rq)


if __name__ == "__main__":
    sock = get_connected_local_socket()

    # send_ssh_keygen_rsa_rq(sock)
    send_ssh_keygen_ed25519_rq(sock)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
        sys.exit(0)

    prv_len = struct.unpack("@I", sock.recv(4))[0]
    prv = sock.recv(prv_len)
    pub_len = struct.unpack("@I", sock.recv(4))[0]
    pub = sock.recv(pub_len)

    print("Private:\n", prv.decode('utf-8'))
    print("Public:\n", pub.decode('utf-8'))

    sock.close()
