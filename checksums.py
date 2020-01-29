from net_common import *
import struct
import sys

def getDirHashOpts(withNames=False,
                   ignoreThumbsFiles=True,
                   ignoreUnixHiddenFiles=True,
                   ignoreEmptyDirs=True):
    return bytearray([((1 if withNames else 0) +
                       (2 if ignoreThumbsFiles else 0) +
                       (4 if ignoreUnixHiddenFiles else 0) +
                       (8 if ignoreEmptyDirs else 0))])

if __name__ == "__main__":
    sock = get_connected_local_socket()

    path = encodeString('/dev/shm/exampleDir')
    # path = encodeString('/dev/null')
    sock.sendall(bytearray(b'\x0A'))  # HASH request
    # sock.sendall(bytearray(b'\x01'))  # choose MD5 algorithm
    sock.sendall(bytearray(b'\x06'))  # choose SHA3-224 algorithm
    sock.sendall(getDirHashOpts(withNames=True,ignoreUnixHiddenFiles=False))  # send dirHashOpts byte (unused for regular files)
    sock.sendall(struct.pack("@H", len(path)))  # len of path as unsigned short
    sock.sendall(path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received, errno is:", struct.unpack("@i", sock.recv(4))[0])
        sys.exit(0)
    # print(toHex(sock.recv(16))) # 128 bit (16 byte) md5 digest size
    print(toHex(sock.recv(28))) # 224 bit (28 byte) sha3-224 digest size
    sock.close()
