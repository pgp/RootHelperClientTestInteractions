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
    s += " copy:\n****************"
    print(s)
    for x in os.listdir(root_dir):
        print(x)
    print("****************\n")


def copyFileOrDir(origin,destination):
    """
    Test copy of a single file or directory onto a destination file or directory
    """
    sock = get_connected_local_socket()

    # printHomeDirContent(rootdir, True)

    #  send delete request for created file
    sock.sendall(b'\x03')  # COPY request
    origin = encodeString(origin)
    destination = encodeString(destination)
    sock.sendall(struct.pack("=H", len(origin)))  # len of path as unsigned short
    sock.sendall(struct.pack("=H", len(destination)))  # len of path as unsigned short
    sock.sendall(origin)
    sock.sendall(destination)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    print('response byte: ', ord(resp))
    if resp != b'\x00':
        print("Error byte received:",struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)

    sock.close()
    # printHomeDirContent(rootdir, False)
    # os.remove(destination)

if __name__ == "__main__":
    # copy ttt dir into qqq (result path: /sdcard/BIGFILES_TEST/qqq/ttt)
    # src_path = '/sdcard/BIGFILES_TEST/ttt'
    src_path = '/sdcard/BIGFILES_TEST/111.rar'

    # dest_path = '/sdcard/BIGFILES_TEST/qqq'
    # dest_path = '/sdcard/BIGFILES_TEST/qqq/ttt'

    # dest_path = '/sdcard/BIGFILES_TEST/222.rar'
    dest_path = '/sdcard/BIGFILES_TEST/333/222.rar'


    copyFileOrDir(src_path,dest_path)
