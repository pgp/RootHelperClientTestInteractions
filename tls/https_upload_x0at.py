import struct
import sys
import os
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from net_common import *
from standalone_xre.xre_common import sendStringWithLen, receiveStringWithLen
import sys


def x0at_upload(sourcePath):
    sock = get_connected_local_socket()

    rq = bytearray(b'\x19')  # ACTION_HTTPS_URL_DOWNLOAD request
    x0at_id = bytearray(b'\x12\x00')
    sock.sendall(rq+x0at_id)

    # send source path
    bDestPath = bytearray(sourcePath.encode("utf-8"))
    sendStringWithLen(sock, bDestPath)

    # No redirect expected from x0.at POST
    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        assert resp == b'\xFF'
        print("Error byte received, errno is:", struct.unpack("@I", sock.recv(4))[0])
        return
    # receive TLS shared session secret hash (64-byte hex encoded SHA256)
    print("TLS master secret hash is:", toHex(sock.recv(32)))

    # receive upload progress
    while True:
        p = struct.unpack("@Q", sock.recv(8))[0]
        if p == 2 ** 64 - 1:
            break
        print("Upload progress:", p)
    print('All data uploaded')

    # [common protocol part, unused here] end-of-redirects
    resp = sock.recv(1)
    assert resp == b'\x11'

    # [common protocol part, unused here] dummy filename
    _ = receiveStringWithLen(sock)
    # response body (a.k.a. download link) size
    size = struct.unpack("@Q", sock.recv(8))[0]
    assert size != 2**64 -1 # expect content size to be well-defined
    generated_link = sock.recv(size)
    print("Generated link: ", generated_link.decode('utf-8').strip())

    return sock

if __name__ == '__main__':
    # create a random file
    path = '/dev/shm/1.bin'
    with open(path, 'wb') as f:
        f.write(os.urandom(10000))
    rclient = x0at_upload(path)
    if rclient is None:
        sys.exit(-1)
    rclient.close()
