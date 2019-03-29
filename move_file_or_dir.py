from net_common import *
import sys
import struct

# originDestinationPairList: list of origin-destination path tuples
def moveFilesOrDirs(originDestinationPairList):
    sock = get_connected_local_socket()

    sock.sendall(bytearray(b'\x02'))  # MOVE request

    # send 0-length-terminated list of path pairs with prepended lengths
    for t_ in originDestinationPairList:
        t = (bytearray(t_[0].encode('utf-8')),bytearray(t_[1].encode('utf-8')))
        sock.sendall(struct.pack("@H", len(t[0])))  # len of path as unsigned short
        sock.sendall(struct.pack("@H", len(t[1])))  # len of path as unsigned short
        sock.sendall(t[0])
        sock.sendall(t[1])
    endOfList = 0
    sock.sendall(struct.pack("@I", endOfList))

    # receive progress, one -1 for each item in the list (non-recursive) plus an ending -2
    completedFiles = 0
    while True:
        progress = struct.unpack("@q", sock.recv(8))[0]
        if progress == -2:
            print("End of transfer")
            break
        if progress == -1:
            print("File or directory moved")
            completedFiles += 1
            continue
        print('Unexpected progress response for move mode, allowed only -1 and -2, exiting...')
        sys.exit(-1)

    # receive response
    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received, errno is:", struct.unpack("@i", sock.recv(4))[0])
    sock.close()

if __name__ == "__main__":
    src_path_1 = '/sdcard/a\nb'
    dest_path_1 = '/sdcard/abc/a\nc'

    src_path_2 = '/sdcard/a\nb1'
    dest_path_2 = '/sdcard/abc/a\nc1'

    tupleList = [(src_path_1, dest_path_1),(src_path_2, dest_path_2)]

    moveFilesOrDirs(tupleList)
