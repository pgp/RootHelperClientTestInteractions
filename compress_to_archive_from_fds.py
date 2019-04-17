# -*- coding: utf-8 -*-
from net_common import *
import struct
import os
from glob import glob
from multiprocessing.reduction import send_handle


def send_fstats(file_list, sock):
    for filepath in file_list:
        st = os.stat(filepath)
        encpath = encodeString(filepath)
        sock.sendall(struct.pack("@H", len(encpath)))  # len of path as unsigned short
        sock.sendall(encpath)
        sock.sendall(struct.pack("@I", st.st_mode))
        sock.sendall(struct.pack("@Q", st.st_size))
        sock.sendall(struct.pack("@Q", int(st.st_atime)))
        sock.sendall(struct.pack("@Q", int(st.st_ctime)))
        sock.sendall(struct.pack("@Q", int(st.st_mtime)))
    sock.sendall(bytearray([0, 0]))  # EOL


def compress_to_archive_with_progress(file_list,
                                      dest_archive_path,
                                      compression_level=9,
                                      encryptFilenames=False,
                                      solidMode=True,
                                      password=None):
    sock = get_connected_local_socket()

    rq = bytearray([ord(b'\x06') ^ (7 << 5)])  # compress from fds

    sock.sendall(rq)

    send_fstats(file_list, sock)

    dest_archive_path = encodeString(dest_archive_path)
    sock.sendall(struct.pack("@H", len(dest_archive_path)))  # len of path as unsigned short
    sock.sendall(dest_archive_path)

    # send compress options
    sock.sendall(struct.pack("@B", compression_level))
    sock.sendall(struct.pack("@B", 1 if encryptFilenames else 0))
    sock.sendall(struct.pack("@B", 1 if solidMode else 0))

    if password is None:
        sock.sendall(struct.pack("@B", 0))  # 1-byte password length
    else:
        password = encodeString(password)
        sock.sendall(struct.pack("@B", len(password)))  # 1-byte password length
        sock.sendall(password)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
        return

    last_progress = 0
    maxuint = 2 ** 64 - 1
    maxuint_2 = 2 ** 64 - 2

    # OK means archive init has been successful, and actual compression starts now, so start receiving progress
    print("OK response received, starting receiving progress updates...")
    # receive total
    total = struct.unpack("@Q", sock.recv(8))[0]  # receive as uint64_t
    print("Received total size:", total)

    while True:
        progress = struct.unpack("@Q", sock.recv(8))[0]
        print("Received progress:", progress)

        if progress == maxuint_2:  # end of compression
            if last_progress == total:  # OK
                print("Compress OK")
            else:
                print("Warning, last progress before termination value differs from total")
            break
        elif progress == maxuint:
            print('Finished compressing file or first iteration')
            # receive index
            idx = struct.unpack("@I", sock.recv(4))[0]
            with open(file_list[idx], 'rb') as f:
                send_handle(sock, f.fileno(), None)
        else:
            last_progress = progress

    # after receiving termination progress value (-1 as uint64), receive standard ok or error response
    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
    else:
        print("OK response received")
    sock.close()


def generateManyFilesInDevShm():
    basepath = '/dev/shm/a/'
    os.makedirs(basepath, exist_ok=True)
    for i in range(1000):
        with open(basepath + f'{i}.bin', 'wb') as f:
            f.write(os.urandom(1000000))
            f.write(os.urandom(ord(os.urandom(1)) * 4 * 1024))


if __name__ == "__main__":
    # os.chdir('/sdcard/iìi')
    # dest_path = '/sdcard/uùu/1àè1.7z'
    # fileListToCompress = ['aàa', 'eèe']

    # many files test
    os.chdir('/dev/shm/a')
    dest_path = '/sdcard/abc.7z'
    fileListToCompress = glob("*.bin")

    password_ = 'qwèrtì'
    compress_to_archive_with_progress(file_list=fileListToCompress,
                                      dest_archive_path=dest_path,
                                      compression_level=9,
                                      solidMode=True,
                                      encryptFilenames=True,
                                      password=password_)
    print('Want to delete created archive? (y/N)')
    s = get_input()
    if s == 'y':
        os.remove(dest_path)
