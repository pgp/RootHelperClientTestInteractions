# -*- coding: utf-8 -*-
from net_common import *
import struct

def compress_to_archive_with_progress(src_folder_path,
                                      dest_archive_path,
                                      compression_level=9,
                                      encryptFilenames=False,
                                      solidMode=True,
                                      fileListOrEntireContent=None,
                                      password=None):
    sock = get_connected_local_socket()

    rq = b'\x06'

    sock.sendall(rq)
    src_folder_path = encodeString(src_folder_path)
    dest_archive_path = encodeString(dest_archive_path)
    sock.sendall(struct.pack("@H", len(src_folder_path)))  # len of path as unsigned short
    sock.sendall(struct.pack("@H", len(dest_archive_path)))  # len of path as unsigned short
    sock.sendall(src_folder_path)
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

    if fileListOrEntireContent is None:  # compress the entire folder content, without the folder entry itself
        sock.sendall(struct.pack("@I", 0))  # number of sent entries to compress is 0, compress entire folder content
    else:
        sock.sendall(struct.pack("@I", len(fileListOrEntireContent)))
        for entry in fileListOrEntireContent:
            entry_ = encodeString(entry)
            sock.sendall(struct.pack("@H", len(entry_)))  # len of path as unsigned short
            sock.sendall(entry_)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
        return

    last_progress = 0
    maxuint64 = 2**64 - 1

    # OK means archive init has been successful, and actual compression starts now, so start receiving progress
    print("OK response received, starting receiving progress updates...")
    # receive total
    total = struct.unpack("@Q", sock.recv(8))[0]  # receive as uint64_t
    print("Received total size:", total)
    while True:
        progress = struct.unpack("@Q", sock.recv(8))[0]
        print("Received progress:", progress)
        if progress == maxuint64:  # end of compression
            if last_progress == total:  # OK
                print("Compress OK")
            else:
                print("Warning, last progress before termination value differs from total")
            break
        last_progress = progress

    # after receiving termination progress value (-1 as uint64), receive standard ok or error response
    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
    else:
        print("OK response received")
    sock.close()


if __name__ == "__main__":
    src_path = '/sdcard/iìi'
    dest_path = '/sdcard/uùu/1àè1.7z'
    fileListToCompress = ['aàa', 'eèe']
    # fileListToCompress = None

    # password_ = 'qwerty'
    password_ = 'qwèrtì'
    # password_ = None
    compress_to_archive_with_progress(src_folder_path=src_path,
                                      dest_archive_path=dest_path,
                                      fileListOrEntireContent=fileListToCompress,
                                      compression_level=9,
                                      solidMode=True,
                                      encryptFilenames=True,
                                      password=password_)
    # os.remove(dest_path)
