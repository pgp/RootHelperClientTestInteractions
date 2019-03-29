from net_common import *
import struct
import sys

# server giving permission denied if run from within CLion
if __name__ == "__main__":
    sock = get_connected_local_socket()

    file_path = encodeString("/sdcard/randfile1")
    # file_path = encodeString("/dev/shm/randfile1") # fallocate won't always work on tmpfs /dev/shm
    fmode = struct.pack("=I", intFromOctalString("0644"))

    #  send create request for given file
    # rq = bytearray([ord(b'\x09') ^ (1 << 5)])  # create file
    # rq = bytearray([ord(b'\x09') ^ (0 << 5)])  # create dir

    # @@@@@@@@@@@@@@
    rq = bytearray([ord(b'\x09') ^ (3 << 5)]) # create file with advanced options (flags 110)

    print("rq is",ord(rq))

    sock.sendall(rq)
    sock.sendall(struct.pack("=H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)
    sock.sendall(fmode)

    # @@@@@@@@@@@@@@
    # creation strategy: 0 fallocate, 1 zeros, 2 random
    #### sock.sendall(b'\x00') # fallocate # not supported by Android API 19, disabled
    # sock.sendall(b'\x01') # zeros
    sock.sendall(b'\x02') # random
    sock.sendall(struct.pack("=Q", 2**30)) # 1 Gb file

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received, errno:",struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)

    sock.close()
