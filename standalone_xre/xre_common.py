from __future__ import print_function
import sys
import os
if not ('.' in sys.path or os.path.realpath('.') in sys.path): sys.path.append(os.path.realpath('.'))
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from rhioutils import *

try:
    import win32api
except ImportError:
    pass

REMOTE_IO_CHUNK_SIZE = 1048576


class vdict(dict):
    def __missing__(self, key):
        value = self[key] = type(self)()
        return value


# LSB of a number
B0 = lambda n: n & 1


# TODO common header with request code, like common_uds.h
ACTION_LS = 0x01
ACTION_CREATE = 0x09
ACTION_STATS = 0x05
ACTION_DOWNLOAD = 0x10
ACTION_UPLOAD = 0x11

"""
Note 1: sys.exit exits thread if invoked from thread
web source: https://stackoverflow.com/questions/905189/why-does-sys-exit-not-exit-when-called-inside-a-thread-in-python
"""


def OSUploadRegularFileWithProgress(srcPath, destPath, fileInfo, conn):
    thisFileSize = fileInfo.st_size
    f = open(srcPath, 'rb') # TODO use try finally or with clause
    print("File size for upload is:", thisFileSize)
    write_fileitem_sock_t(conn, (b'\x00', destPath, thisFileSize))

    quotient, remainder = thisFileSize // REMOTE_IO_CHUNK_SIZE, thisFileSize % REMOTE_IO_CHUNK_SIZE

    print('Chunk info: quotient is:', quotient, ', remainder is:', remainder)

    # BEGIN quotient + remainder IO loop
    for _ in range(0, quotient):
        chunk = readAllOrExit(f, REMOTE_IO_CHUNK_SIZE)
        conn.sendall(chunk)
    if remainder != 0:
        chunk = readAllOrExit(f, remainder)
        conn.sendall(chunk)
    # END quotient + remainder IO loop
    f.close()  # TODO use try finally or with clause


# actually with no progress, just to follow names from RH C++ code
def genericUploadBasicRecursiveImplWithProgress(srcPath, destPath, conn):
    if os.path.isdir(srcPath):
        # send empty dir item to network descriptor
        if os.listdir(srcPath):
            for item in os.listdir(srcPath):
                genericUploadBasicRecursiveImplWithProgress(os.path.join(srcPath, item),
                                                            os.path.join(destPath, item),
                                                            conn)
        else:  # empty dir
            conn.sendall(b'\x01')
            sendStringWithLen(conn, windowsToUnixPath(destPath))
    elif os.path.isfile(srcPath):
        fileInfo = os.stat(srcPath)
        OSUploadRegularFileWithProgress(srcPath, destPath, fileInfo, conn)


def countTotalStatsIntoMap(path, m):
    # tFiles,tFolders,tSize = 0,0,0 all 64-bit unsigned
    tItems = [0, 0, 0]

    try:
        filestats = os.stat(path)
    except:
        print("Access error to ", path, ",skipping...")
        m[path] = tItems
        return tItems  # in any case of access error, do not count the file

    if os.path.isfile(path):
        tItems[0] += 1  # tFiles
        tItems[2] = filestats.st_size  # tSize
        m[path] = tItems
        return tItems

    tItems[1] += 1

    for filename in os.listdir(path):
        childpath = os.path.join(path, filename)
        if os.path.isdir(childpath):
            subnum = countTotalStatsIntoMap(childpath, m)
            tItems[0] += subnum[0]  # tFiles
            tItems[1] += subnum[1]  # tFolders
            tItems[2] += subnum[2]  # tSize
        elif os.path.isfile(childpath):
            tItems[0] += 1
    m[path] = tItems
    return tItems


def receivePathPairsList(conn):
    v = []
    while True:
        lx = struct.unpack("@H", conn.recv(2))[0]
        ly = struct.unpack("@H", conn.recv(2))[0]
        if lx == 0: break
        v.append((unixToWindowsPath(conn.recv(lx)), unixToWindowsPath(conn.recv(ly))))
    return v


def sendPathPairList(conn, *pathpairs):
    for pathpair in pathpairs:
        # send the two path lengths
        conn.sendall(struct.pack("@H", len(pathpair[0])))
        conn.sendall(struct.pack("@H", len(pathpair[1])))
        # send the two paths
        conn.sendall(pathpair[0])
        conn.sendall(pathpair[1])
    conn.sendall(bytearray([0, 0, 0, 0]))  # send end of list


# content of item: flag(file/dir), filepath string, size

# 0: file, 1: folder, FF: end of list
def read_fileitem_sock_t(conn):
    flag = conn.recv(1)
    if flag == b'\xFF': return flag, None, None
    pathname = unixToWindowsPath(receiveStringWithLen(conn))
    size = 0 if flag == b'\x01' else struct.unpack("@Q", conn.recv(8))[0]
    return flag, pathname, size


def write_fileitem_sock_t(conn, item):
    conn.sendall(item[0])  # flag (1 byte)
    sendStringWithLen(conn, windowsToUnixPath(item[1]))  # filepath as string
    conn.sendall(struct.pack('@Q', item[2]))  # size (8 byte)


class ItemWithContent(object):
    def __init__(self, rpath: str, wpath: str) -> None:
        self.isDir = os.path.isdir(rpath)
        if not self.isDir:
            self.flag = b'\x00'
            self.size = os.stat(rpath).st_size
        else:
            self.flag = b'\x01'
            self.size = 0
        self.rpath = rpath
        self.wpath = wpath

    @staticmethod
    def eol(conn):
        conn.sendall(b'\xFF')

    @staticmethod
    def read(conn) -> bool:
        flag = conn.read(1)
        if flag == b'\x00':
            wpath = standardizeFromXrePath(receiveStringWithLen(conn))
            size = struct.unpack("@Q", conn.recv(8))[0]
            print('Receiving file', wpath, 'of size', size)
            os.makedirs(os.path.dirname(wpath), exist_ok=True)
            assert size > 0
            chunkSize = 1024
            remaining = size
            currentProgress = 0
            lastProgress = 0
            with open(wpath, 'wb') as g:
                while True:
                    readBytes = conn.read(min(chunkSize, remaining))
                    if not readBytes:
                        raise ConnectionError('Connection closed while downloading')
                    g.write(readBytes)
                    remaining -= len(readBytes)
                    currentProgress += len(readBytes)
                    if currentProgress - lastProgress > 1000000:
                        print('Received', currentProgress, 'bytes for file', wpath)
                        lastProgress = currentProgress
                    if remaining < 0:
                        raise ValueError('Out of bounds reading bytes')
                    if remaining == 0:
                        break
            return True
        elif flag == b'\x01':
            wpath = standardizeFromXrePath(receiveStringWithLen(conn))
            print('directory',wpath)
            return True
        elif flag == b'\xFF':
            print('End of files')
            return False
        else:
            raise ValueError('Invalid flag byte for ItemWithContent')

    def write(self, conn):
        currentProgress = 0
        lastProgress = 0
        conn.sendall(self.flag)  # flag (1 byte)
        sendStringWithLen(conn, standardizeToXrePath(self.wpath))  # filepath as string
        if not self.isDir:  # regular file
            print('Sending', self.rpath, 'of size', self.size)
            conn.sendall(struct.pack('@Q', self.size))  # size (8 byte)
            # send file content
            with open(self.rpath, 'rb') as f:
                while True:
                    readBytes = f.read(REMOTE_IO_CHUNK_SIZE)
                    if not readBytes: break
                    conn.sendall(readBytes)
                    currentProgress += len(readBytes)
                    if currentProgress - lastProgress > 1000000:
                        lastProgress = currentProgress
                        print('Sent', len(readBytes), 'bytes for file', self.rpath, 'progress:', currentProgress)

#############################################################

def receiveStringWithLen(conn):
    filenamelen = struct.unpack("@H", conn.recv(2))[0]
    return conn.recv(filenamelen)

# generalization to python 3:
#  accept str/bytes/bytearray (implicit) for python 2
#  accept bytes/bytearray for python 3
def sendStringWithLen(conn, s):
    conn.sendall(struct.pack("@H", len(s)))  # assumed bytes in UTF-8 encoding
    conn.sendall(s)


def sendOkResponse(conn):
    conn.send(b'\x00')


def sendErrorResponse(conn, errno):
    conn.send(b'\xFF')
    conn.sendall(struct.pack("@i", errno))


###########################


def listDir(conn, rqflagsunused):
    # client must send paths in posix format (C:\path becomes /C:/path) and UTF-8 encoding
    dirpath = unixToWindowsPath(receiveStringWithLen(conn))

    children = []

    if os.name == 'nt':
        if dirpath == '':
            children = [x.replace('\\', '') for x in win32api.GetLogicalDriveStrings().split('\000')[:-1]]

    try:
        if not children:
            children = os.listdir(dirpath)
        sendOkResponse(conn)
    except OSError as oser:
        traceback.print_exc()
        sendErrorResponse(conn, oser.errno)
        return

    for filename in children:
        try:
            filestat = os.stat(os.path.join(dirpath, filename))
        except OSError as oser:
            print('error in stat of:', filename)
            print(oser)
            continue
        sendStringWithLen(conn, filename.encode('utf-8') if ((type(filename) is unicode and unicode is not None) or (type(filename) is str and unicode is None)) else filename)
        conn.sendall(struct.pack("@I", int(filestat.st_mtime)))
        conn.sendall("d---------".encode('utf-8') if os.path.isdir(os.path.join(dirpath, filename)) else "----------".encode('utf-8'))
        conn.sendall(struct.pack("@Q", int(filestat.st_size)))
        print('sent item info for:', filename)

    # EOL indication
    conn.sendall(struct.pack("@H", 0))


def createFileOrDirectory(conn, rqflags):
    # read len and path
    filename = receiveStringWithLen(conn)
    filemode = struct.unpack("@i", conn.recv(4))[0]
    try:
        if B0(rqflags):
            print('creating file...')
            parentDir = os.path.dirname(filename)
            if not os.path.exists(parentDir):
                os.makedirs(parentDir, filemode)
            fd = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL, filemode)
            os.close(fd)
        else:
            print('creating directory...')
            os.makedirs(filename, filemode)
        sendOkResponse(conn)
    except OSError as oser:
        sendErrorResponse(conn, oser.errno)


def stats(conn, rqflags):
    raise BaseException('STATS NOT IMPLEMENTED')


# server handles client download request, i.e. server uploads to client
def server_download(conn, rqflagsunused):
    v = receivePathPairsList(conn)
    descendantCountMap = vdict()
    counts = [0, 0, 0]

    for pathpair in v:
        itemTotals = countTotalStatsIntoMap(pathpair[0], descendantCountMap)
        counts[0] += itemTotals[0]
        counts[1] += itemTotals[1]
        counts[2] += itemTotals[2]

    conn.sendall(struct.pack("@Q", counts[0]))  # tFiles
    conn.sendall(struct.pack("@Q", counts[2]))  # tSize

    for pathpair in v:
        genericUploadBasicRecursiveImplWithProgress(pathpair[0], pathpair[1], conn)

    conn.sendall(b'\xFF')  # EOL indication to remote socket


# client sends UPLOAD request
def downloadRemoteItems(conn, rqflagsunused):
    while True:
        flag, pathname, size = read_fileitem_sock_t(conn)
        if flag == b'\xFF': break
        if flag == b'\x00':
            try:
                parentdir = os.path.dirname(pathname)
                if not os.path.exists(parentdir):
                    os.makedirs(parentdir)
                f = open(pathname, 'wb')
            except:
                traceback.print_exc()
                print('Unable to open destination file for writing:', pathname)
                continue
            # BEGIN quotient + remainder IO loop
            quotient, remainder = size // REMOTE_IO_CHUNK_SIZE, size % REMOTE_IO_CHUNK_SIZE
            for i in range(0, quotient):
                chunk = readAllOrExit(conn, REMOTE_IO_CHUNK_SIZE)
                f.write(chunk)
            if remainder != 0:
                chunk = readAllOrExit(conn, remainder)
                f.write(chunk)
            # END quotient + remainder IO loop
            f.close()

        elif flag == b'\x01':
            try:
                os.makedirs(pathname)
            except OSError as oser:
                print(oser)
                print('Unable to create directory:', pathname)
        else:
            print('Unexpected file item flag, exiting thread...')
            conn.close()
            sys.exit(-1)


def defaultServerAction(conn, rqflagsunused):
    conn.close()
    print("Unexpected data received, disconnected client")
    sys.exit(0)  # Note 1


actionDict = {ACTION_LS: listDir,
              ACTION_CREATE: createFileOrDirectory,
              ACTION_STATS: stats,
              ACTION_DOWNLOAD: server_download,
              ACTION_UPLOAD: downloadRemoteItems}


def xre_server_session(conn):
    while True:
        try:
            # read request byte
            rqAndFlags = struct.unpack("@B", conn.recv(1))[0]
            rq, flags = (rqAndFlags & 31, rqAndFlags >> 5)
            try:
                f = actionDict[rq]
            except KeyError:
                print('Key not found in actionDict:', rq)
                f = defaultServerAction
            f(conn, flags)  # has to catch any OSError
        # except IOError as e:
        except:
            traceback.print_exc()
            conn.shutdown(socket.SHUT_RDWR)
            conn.close()
            print("Client disconnected itself from server")
            return
