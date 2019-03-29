from net_common import *
import struct
import os

# Copy Tags
EOF = 2**64 -1
EOFs = 2**64 -2
CFL = 2**64 -3  # conflict
ERR = 2**64 -4  # unsolvable error

# originDestinationPairList: list of origin-destination path tuples
def copyFileOrDirWithProgressNoConflicts(originDestinationPairList):
    """
    Test copy of a single file or directory onto a destination file or directory with inner and outer progress
    No conflict handling implemented
    """
    sock = get_connected_local_socket()

    sock.sendall(b'\x03')  # COPY request

    # send 0-length-terminated list of path pairs with prepended lengths
    for t in originDestinationPairList:
        sock.sendall(struct.pack("@H", len(t[0])))  # len of path as unsigned short
        sock.sendall(struct.pack("@H", len(t[1])))  # len of path as unsigned short
        sock.sendall(t[0])
        sock.sendall(t[1])
    endOfList = 0
    sock.sendall(struct.pack("@I", endOfList))

    totalFiles = struct.unpack("@Q", sock.recv(8))[0]
    currentFiles = 0

    print('total non-directory files:', totalFiles)

    # receive progresses
    hasReceivedSizeForcurrentFile = False # set to false after an EOF, and at the beginning
    while True:
        currentProgress = struct.unpack("@Q", sock.recv(8))[0]
        if currentProgress == EOF:
            print("File completed")
            hasReceivedSizeForcurrentFile = False
            currentFiles += 1
        elif currentProgress == EOFs:
            print("Received end of transfer")
            break
        else:
            # inner progress, print size or progress
            if hasReceivedSizeForcurrentFile:
                print("Current file:", currentFiles, "\tCurrent progress:", currentProgress)
            else:
                print("Current file:", currentFiles, "\tReceived file size:", currentProgress)
                hasReceivedSizeForcurrentFile = True

    sock.close()
    # printHomeDirContent(rootdir, False)
    # os.remove(destination)

def doSingleFileCopy():
    src_path = '/sdcard/BIGFILES_TEST/big.7z'
    dest_path = '/sdcard/BIGFILES_TEST/filecopied/big.7z'
    tupleList = [(src_path, dest_path)]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def doSingleFolderCopy():
    src_path = '/sdcard/BIGFILES_TEST/fewbigfiles'
    dest_path = '/sdcard/BIGFILES_TEST/fewbigfiles_copied'
    tupleList = [(src_path, dest_path)]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def doMultipleFilesCopy():
    tupleList = [('/sdcard/BIGFILES_TEST/nonsolid_m3.7z','/sdcard/BIGFILES_TEST/multiCopied/nonsolid_m3.7z'),
                 ('/sdcard/BIGFILES_TEST/fewbigfiles', '/sdcard/BIGFILES_TEST/multiCopied/fewbigfiles'),
                 ('/sdcard/BIGFILES_TEST/ttt', '/sdcard/BIGFILES_TEST/multiCopied/ttt')]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def cleanupFilesAndFolders():
    os.system('rm -rf /sdcard/BIGFILES_TEST/filecopied/*')
    os.system('rm -rf /sdcard/BIGFILES_TEST/multiCopied/*')
    os.system('rm -rf /sdcard/BIGFILES_TEST/fewbigfiles_copied')

if __name__ == "__main__":
    # cleanupFilesAndFolders()
    doSingleFileCopy()
    # doSingleFolderCopy()
    # doMultipleFilesCopy()
