from net_common import *
import os

from fileCopy_socketStatusMap import *

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
    totalSize = struct.unpack("@Q", sock.recv(8))[0]

    print('Total non-directory files:', totalFiles)
    print('Total size in items:', totalSize)

    # receive progresses
    fileCopyProgress(sock)

    sock.close()
    # printHomeDirContent(rootdir, False)
    # os.remove(destination)

def doSingleFileCopy():
    src_path = '/sdcard/BIGFILES_TEST/f0.bin'
    dest_path = '/sdcard/BIGFILES_TEST/filecopied/f0.bin'
    tupleList = [(src_path, dest_path)]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def doSingleFolderCopy():
    src_path = '/sdcard/BIGFILES_TEST/singlefolder'
    dest_path = '/sdcard/BIGFILES_TEST/cp/singlefolder'
    tupleList = [(src_path, dest_path)]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def doFoldersOnlyCopy():
    tupleList = [('/sdcard/BIGFILES_TEST/singlefolder', '/sdcard/BIGFILES_TEST/cp/singlefolder'),
                 ('/sdcard/BIGFILES_TEST/singlefolder1', '/sdcard/BIGFILES_TEST/cp/singlefolder1'),]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def doMultipleFilesCopy():
    tupleList = [('/sdcard/BIGFILES_TEST/f1.bin','/sdcard/BIGFILES_TEST/multiCopied/f1.bin'),
                 ('/sdcard/BIGFILES_TEST/fewbigfiles', '/sdcard/BIGFILES_TEST/multiCopied/fewbigfiles'),
                 ('/sdcard/BIGFILES_TEST/ttt', '/sdcard/BIGFILES_TEST/multiCopied/ttt')]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def doFilesOnlyCopy():
    tupleList = [('/sdcard/BIGFILES_TEST/f0.bin','/sdcard/BIGFILES_TEST/filesOnlyCopied/f0.bin'),
                 ('/sdcard/BIGFILES_TEST/f1.bin', '/sdcard/BIGFILES_TEST/filesOnlyCopied/f1.bin'),
                 ('/sdcard/BIGFILES_TEST/f6.dat', '/sdcard/BIGFILES_TEST/filesOnlyCopied/f6.dat'),
                 ('/sdcard/BIGFILES_TEST/f8.abc', '/sdcard/BIGFILES_TEST/filesOnlyCopied/f8.abc'),
                 ('/sdcard/BIGFILES_TEST/f2.dat', '/sdcard/BIGFILES_TEST/filesOnlyCopied/f2.dat')]
    copyFileOrDirWithProgressNoConflicts(tupleList)

def cleanupFilesAndFolders():
    os.system('rm -rf /sdcard/BIGFILES_TEST/filecopied/*')
    os.system('rm -rf /sdcard/BIGFILES_TEST/multiCopied/*')
    os.system('rm -rf /sdcard/BIGFILES_TEST/filesOnlyCopied/*')
    os.system('rm -rf /sdcard/BIGFILES_TEST/fewbigfiles_copied')

if __name__ == "__main__":
    # cleanupFilesAndFolders()
    doSingleFileCopy()
    # doFilesOnlyCopy()
    # doSingleFolderCopy()
    # doFoldersOnlyCopy()
    # doMultipleFilesCopy()
