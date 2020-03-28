# -*- coding: utf-8 -*-
from net_common import *
import struct
import sys
from datetime import datetime

str1 = "\0theroothelper"

class IndexListForRelativeExtract:
    def __init__(self,stripPathLen=0,indexList=list()):
        self.stripPathLen = stripPathLen
        self.indexList = indexList

def ls_archive(src_archive_path, password=None):
    sock = get_connected_local_socket()

    rq = bytearray([ord(b'\x01') ^ (7 << 5)])  # all flag bits set (ls archive)

    src_archive_path = encodeString(src_archive_path)
    sock.sendall(rq)
    sock.sendall(struct.pack("@H", len(src_archive_path)))  # len of path as unsigned short
    sock.sendall(src_archive_path)

    if password is None:
        sock.sendall(struct.pack("@B", 0))  # 1-byte password length
    else:
        password = encodeString(password)
        sock.sendall(struct.pack("@B", len(password)))  # 1-byte password length
        sock.sendall(password)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
        sys.exit(0)
    cnt = []
    while True:
        ll = struct.unpack("@H", sock.recv(2))[0]  # receive file entry (filename) length
        if ll == 0: break
        print("response entry list length is",ll)
        fname = sock.recv(ll).decode('latin-1')  # receive file entry (filename)
        fdate = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
        fperms = sock.recv(10).decode('utf-8')
        fsize = struct.unpack("@Q", sock.recv(8))[0]

        cnt.append((fname, fdate, fperms, fsize))
        print(fname + '\t' + str(fdate) + '\t' + fperms + '\t' + str(fsize))
    sock.close()


def extract_archive_with_progress(src_archive_path, dest_folder_path, indexListOrEntireContent=None, password=None, smartDirectoryCreation=False):
    sock = get_connected_local_socket()

    rq = bytearray([ord(b'\x07') ^ ((6 if smartDirectoryCreation else 0) << 5)])

    sock.sendall(rq)
    src_archive_path, dest_folder_path = encodeString(src_archive_path),encodeString(dest_folder_path)
    sock.sendall(struct.pack("@H", len(src_archive_path)))  # len of path as unsigned short
    sock.sendall(struct.pack("@H", len(dest_folder_path)))  # len of path as unsigned short
    sock.sendall(src_archive_path)
    sock.sendall(dest_folder_path)

    if password is None:
        sock.sendall(struct.pack("@B", 0))  # 1-byte password length
    else:
        password = encodeString(password)
        sock.sendall(struct.pack("@B", len(password)))  # 1-byte password length
        sock.sendall(password)

    if indexListOrEntireContent is None:
        # send numOfItems 0 to indicate that all content has to be extracted
        sock.sendall(struct.pack("@I", 0))  # numOfItems as unsigned int
    else:
        sock.sendall(struct.pack("@I", len(indexListOrEntireContent.indexList)))  # numOfItems as unsigned int
        for i in indexListOrEntireContent.indexList:
            sock.sendall(struct.pack("@I", i))
        # send common prefix len in wide chars
        sock.sendall(struct.pack("@I", indexListOrEntireContent.stripPathLen))

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
        return

    last_progress = 0
    maxuint64 = 2 ** 64 - 1

    # OK means archive init has been successful, and actual compression starts now, so start receiving progress
    print("OK response received, starting receiving progress updates...")
    # receive total
    total = struct.unpack("@Q", sock.recv(8))[0]  # receive as uint64_t
    print("Received total size: ", total)
    while True:
        progress = sock.recv(8)
        progress = struct.unpack("@Q", progress)[0]
        print("Received progress: ", progress)
        if progress == maxuint64:  # end of compression
            if last_progress == total:  # OK
                print("Extract OK")
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
    # archive_path = '/sdcard/BIGFILES_TEST/special/winUtf.7z'  # decode to latin-1
    # archive_path = '/sdcard/BIGFILES_TEST/special/unixUtf.7z'  # decode to latin-1
    # archive_path = '/sdcard/BIGFILES_TEST/special/1special.7z'
    # archive_path = '/sdcard/BIGFILES_TEST/special/1special.rar'
    # archive_path = '/sdcard/BIGFILES_TEST/ttt.7z'
    # archive_path = '/sdcard/BIGFILES_TEST/special/files.zip'
    # archive_path = '/sdcard/BIGFILES_TEST/rar/rar3.rar'
    # archive_path = '/sdcard/BIGFILES_TEST/rar/rar5.rar'
    # archive_path = '/sdcard/BIGFILES_TEST/apk.zip'

    # archive_path = '/sdcard/BIGFILES_TEST/archiveTypes/plain/gz.tar.gz'
    # ls_archive(archive_path)
    # sys.exit(0)

    # FIXME: non-existing file returning same error code as unsupported file type
    # archive_path = '/sdcard/BIGFILES_TEST/notanarchive.txt'
    # archive_path = '/sdcard/BIGFILES_TEST/notexisting'

    # password-protected file, no password provided
    # archive_path = '/sdcard/BIGFILES_TEST/qwerty_password_encrypted_listing.7z'
    # archive_path = '/sdcard/BIGFILES_TEST/qwerty_password_plain_listing.7z'

    # extract all, plain filenames, encrypted content, wrong password
    #~ archive_path = '/sdcard/BIGFILES_TEST/archiveTypes/enc/7zaes_plainnames.7z'
    #~ dest_path = '/sdcard/BIGFILES_TEST/archiveTypes/enc/7zaes'
    #~ extract_archive_with_progress(src_archive_path=archive_path,
                                  #~ dest_folder_path=dest_path,
                                  #~ password='qwerty')
	
    # archive_path = '/sdcard/BIGFILES_TEST/special/unixUtf.7z'
    # archive_path = '/sdcard/BIGFILES_TEST/t3.7z'

    # archive_path = '/sdcard/BIGFILES_TEST/archiveTypes/plain/rar5.rar'
    # dest_path = '/sdcard/BIGFILES_TEST/t3t3'

    # archive_path = '/sdcard/uùu/1àè1.7z'
    # dest_path = '/sdcard/uàuàuà'

    # extract_archive_with_progress(src_archive_path=archive_path,
    #                               dest_folder_path=dest_path)

    # archive_path = '/sdcard/BIGFILES_TEST/aa.7z'
    # dest_path = '/sdcard/BIGFILES_TEST/aabb'
    # extract_archive_with_progress(src_archive_path=archive_path,
    #                               dest_folder_path=dest_path)

    # extract_archive_with_progress(src_archive_path=archive_path,
    #                               dest_folder_path=dest_path)

    # ls_archive(src_archive_path=archive_path, password='qwerty')
    # ls_archive(src_archive_path=archive_path)

    # extract all
    # extract_archive_with_progress(src_archive_path='/sdcard/BIGFILES_TEST/ttt.7z',
    #                      dest_folder_path='/sdcard/BIGFILES_TEST/tttExtracted')

    # selective extract (C-style indices from ordered list in output from ls_archive
    # extract_archive_with_progress(src_archive_path='/sdcard/BIGFILES_TEST/t3.7z',
    #                      dest_folder_path='/sdcard/BIGFILES_TEST/tttExtracted',
    #                      password='qwerty',
    #                      indexListOrEntireContent=IndexListForRelativeExtract(6,[10, 11]))

    # extract all files with smart directory creation
    extract_archive_with_progress(src_archive_path='/sdcard/1.7z',
                                  dest_folder_path='/sdcard/tttExtracted',
                                  smartDirectoryCreation=True)

    # extract_archive_with_progress(src_archive_path=archive_path,
    #                      dest_folder_path='/sdcard/BIGFILES_TEST/encExtracted',
    #                      password='qwerty')

    # testing extract from stream archives and assigning virtual inner name
    # extract_archive_with_progress(src_archive_path='/sdcard/BIGFILES_TEST/archiveTypes/plain/xz.tar.xz',
    #                               dest_folder_path='/sdcard/extracted')
    # extract_archive_with_progress(src_archive_path='/sdcard/BIGFILES_TEST/archiveTypes/plain/bz2.tar.bz2',
    #                               dest_folder_path='/sdcard/extracted')
    # extract_archive_with_progress(src_archive_path='/sdcard/BIGFILES_TEST/archiveTypes/plain/gz.tar.gz',
    #                               dest_folder_path='/sdcard/extracted')
