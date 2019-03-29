from net_common import *
import struct
import sys
import os


def printHomeDirContent(root_dir, beforeOrAfter):
    s = "Directory content "
    if beforeOrAfter:
        s += "before"
    else:
        s += "after"
    s += " delete:\n****************"
    print(s)
    for x in os.listdir(root_dir):
        print(x)
    print("****************\n")


def createFile(file_to_be_created):
    # create file
    f = open(file_to_be_created, "a")
    f.close()


def deleteFileOrDir(file_path):
    sock = get_connected_local_socket()

    file_path = encodeString(file_path)
    sock.sendall(b'\x04')  # DEL request
    sock.sendall(struct.pack("@H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
    else:
        print("OK response received")
    sock.close()


def oldDeleteTestCase():
    sock = get_connected_local_socket()

    rootdir = "/sdcard/"
    file_path = rootdir + "tmpfile"
    folder_path = rootdir + "ttt"

    createFile(file_path)

    printHomeDirContent(rootdir, True)

    #  send delete request for created file
    file_path = encodeString(file_path)
    sock.sendall(b'\x04')  # DEL request
    sock.sendall(struct.pack("@H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
        sys.exit(0)

    sock.close()

    # send delete request for a non-empty directory
    sock = get_connected_local_socket()

    #  send delete request for created file
    folder_path = encodeString(folder_path)
    sock.sendall(b'\x04')  # DEL request
    sock.sendall(struct.pack("@H", len(folder_path)))  # len of path as unsigned short
    sock.sendall(folder_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:", struct.unpack("=i", sock.recv(4)))
        sys.exit(0)

    sock.close()
    printHomeDirContent(rootdir, False)

if __name__ == "__main__":
    path = "/sdcard/fewbigfiles_copied"
    deleteFileOrDir(path)
