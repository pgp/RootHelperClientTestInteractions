from datetime import datetime
from net_common import *
import sys

import struct

def list_dir(sock, path='/'):
    path = encodeString(path)
    sock.sendall('\x01')  # LS request
    sock.sendall(struct.pack("@H", len(path)))  # len of path as unsigned short
    sock.sendall(path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
        sys.exit(-1)
    cnt = []
    while True:
        ll = struct.unpack("@H", sock.recv(2))[0]  # receive file entry (filename) length
        if ll == 0: break
        fname = sock.recv(ll).decode('utf-8')  # receive file entry (filename)
        fdate = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
        fperms = sock.recv(10).decode('utf-8')
        fsize = struct.unpack("@Q", sock.recv(8))[0]

        cnt.append((fname, fdate, fperms, fsize))
        print(fname + '\t' + str(fdate) + '\t' + fperms + '\t' + str(fsize))


UPLOAD = False
DOWNLOAD = True
def upload_or_download_items(sock, downloadOrUpload, *pathpairs):
    rq_byte = b'\x10' if downloadOrUpload is DOWNLOAD else b'\x11'
    sock.sendall(rq_byte)
    for p in pathpairs:
        pathpair = (encodeString(p[0]), encodeString(p[1]))
        # send the two path lengths
        sock.sendall(struct.pack("@H",len(pathpair[0])))
        sock.sendall(struct.pack("@H", len(pathpair[1])))
        # send the two paths
        sock.sendall(pathpair[0])
        sock.sendall(pathpair[1])
    sock.sendall(bytearray([0,0,0,0])) # send end of list

    # read total number of files for updating external progress
    print("Total files: ", struct.unpack("@Q", sock.recv(8))[0])
    currentFiles = 0

    # receive progresses
    hasReceivedSizeForcurrentFile = False  # set to false after an EOF, and at the beginning
    while True:
        currentProgress = struct.unpack("@Q", sock.recv(8))[0]
        if currentProgress == 2 ** 64 - 1:
            print("File completed")
            hasReceivedSizeForcurrentFile = False
            currentFiles += 1
        elif currentProgress == 2 ** 64 - 2:
            print("Received end of transfer")
            break
        else:
            # inner progress, print size or progress
            if hasReceivedSizeForcurrentFile:
                print("Current file:", currentFiles, "\tCurrent progress:", currentProgress)
            else:
                print("Current file:", currentFiles, "\tReceived file size:", currentProgress)
                hasReceivedSizeForcurrentFile = True


def remote_client(serverHost="192.168.43.1",serverPort=11111):
    sock = get_connected_local_socket("anotherRoothelper")

    rq = b'\x14'
    sock.sendall(rq) # REMOTE_CONNECT request

    # send string-with-length of IP
    serverHost = encodeString(serverHost)
    sock.sendall(struct.pack("@B",len(serverHost)))
    sock.sendall(serverHost)
    # send port
    sock.sendall(struct.pack("@H",serverPort))

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
        return
    return sock



if __name__ == '__main__':
    rclient = remote_client(serverHost="192.168.169.170", serverPort=11111)
    if rclient is None:
        sys.exit(-1)

    # list_dir(sock=rclient, path='/')

    # upload_items(rclient,
    #              ('/sdcard/BIGFILES_TEST/t3.7z', '/sdcard/BIGFILES_TEST/remote/t3.7z'))

    # print "............................"
    # print "..........sleeping.........."
    # print "............................"
    # sleep(3)

    # upload_or_download_items(rclient,
    #                          UPLOAD,
    #              ('/sdcard/BIGFILES_TEST/t3.7z','/sdcard/BIGFILES_TEST/remote/t3.7z'),
    #              ('/sdcard/BIGFILES_TEST/ttt.7z', '/sdcard/BIGFILES_TEST/remote/ttt.7z'),
    #              ('/sdcard/BIGFILES_TEST/solid_m3.7z', '/sdcard/BIGFILES_TEST/remote/solid_m3.7z'),
    #              ('/sdcard/BIGFILES_TEST/ttt','/sdcard/BIGFILES_TEST/remote/ttt'))

    upload_or_download_items(rclient,
                             DOWNLOAD,
                             ('/sdcard/BIGFILES_TEST/t3.7z', '/sdcard/BIGFILES_TEST/local/t3.7z'),
                             ('/sdcard/BIGFILES_TEST/ttt.7z', '/sdcard/BIGFILES_TEST/local/ttt.7z'),
                             ('/sdcard/BIGFILES_TEST/solid_m3.7z', '/sdcard/BIGFILES_TEST/local/solid_m3.7z'),
                             ('/sdcard/BIGFILES_TEST/ttt', '/sdcard/BIGFILES_TEST/local/ttt'))

    # list_dir(sock=rclient, path='/sdcard')

    rclient.close()
