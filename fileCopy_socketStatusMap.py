import struct
import sys
from net_common import *

currentStatus = None
copyRunning = True

#############################################################
# duplicated from rhioutils.py

def receiveStringWithLen(conn):
    filenamelen = struct.unpack("@H", conn.recv(2))[0]
    return conn.recv(filenamelen).decode("utf-8")


def sendStringWithLen(conn, s):
    s = encodeString(s)
    conn.sendall(struct.pack("@H", len(s)))
    conn.sendall(s)


def sendOkResponse(conn):
    conn.send(b'\x00')


def sendErrorResponse(conn, errno):
    conn.send(b'\xFF')
    conn.sendall(struct.pack("@i", errno))


###########################

# duplicated code
# Copy Tags
EOF = 2**64 -1
EOFs = 2**64 -2
CFL = 2**64 -3  # conflict
ERR = 2**64 -4  # unsolvable error
SKIP = 2**64 -5 # for incrementing total files progress on SKIP_ALL permanent decision set after skipping a dir or a file
SIZE = "SIZE"
PROGRESS = "PROGRESS"

#conflict types
CONFLICT_TYPE_FILE = b'\x00'
CONFLICT_TYPE_DIR = b'\x01'

# conflict decisions, copied from cfl resp.h
CD_SKIP = b'\x00'
CD_SKIP_ALL = b'\x10'
CD_OVERWRITE = b'\x01'
CD_OVERWRITE_ALL = b'\x11'
CD_REN_SRC = b'\x02' # followed by filename_sock_t containing new name
CD_REN_DEST = b'\x03' # followed by filename_sock_t containing new name
CD_REN_SRC_ALL = b'\x12'
CD_REN_DEST_ALL = b'\x13'
# for folders over existing folders
CD_MERGE = b'\x04'
CD_MERGE_RECURSIVE = b'\x14'
CD_MERGE_ALL = b'\x24'

CD_CANCEL = b'\x05'

NO_PREV_DEC = b'\xFF'

ED_CONTINUE = b'\x00'
ED_CANCEL = b'\xFF'

allowedUserDecs = frozenset([
    CD_SKIP,
    CD_SKIP_ALL,
    CD_OVERWRITE,
    CD_OVERWRITE_ALL,
    CD_REN_SRC,
    CD_REN_DEST,
    CD_REN_SRC_ALL,
    CD_REN_DEST_ALL,
    CD_MERGE,
    CD_MERGE_ALL,
    CD_CANCEL
])

allowedErrorDecs = frozenset([ED_CONTINUE,ED_CANCEL])

# returns must be tail-call optimized, so they can't be used here

def fromEOF(sock): # -> EOFs, CFL, ERR
    global currentStatus
    n = struct.unpack("@Q", sock.recv(8))[0]
    if n < 2 ** 64 - 5:  # it's SIZE
        # return fromSIZE(sock)
        currentStatus = SIZE
    else:
        # return transitionMap[n](sock)
        currentStatus = n

def fromEOFs(sock):
    global copyRunning
    print('Received EOFs, all done, exiting...')
    copyRunning = False


def commonTransition(sock):
    global currentStatus
    n = struct.unpack("@Q", sock.recv(8))[0]
    if n < 2 ** 64 - 5:  # SIZE
        print('Size is', n)
        # return fromSIZE(sock)
        currentStatus = SIZE
    else:
        # return transitionMap[n](sock) # EOFs
        if n != EOFs and n != ERR and n != CFL and n != SKIP:
            raise RuntimeError("Expected EOFs, ERR, CFL or SKIP here, protocol error, n is " + str(n))
        currentStatus = n


def fromCFL(sock): # -> SIZE, EOFs, CFL, ERR
    global currentStatus
    # receive conflict type (FILE over something vs DIR over something)
    # cflType = sock.recv(1)

    # receive involved paths
    x = receiveStringWithLen(sock)
    y = receiveStringWithLen(sock)

    xtype = sock.recv(1) # == cflType
    ytype = sock.recv(1)

    print('Conflict type is ', ('FILE' if xtype == CONFLICT_TYPE_FILE else 'DIR'))

    print('Conflicting paths are: ',
          x, ' of type ', ('DIR' if xtype == b'\x01' else 'FILE'), ' , ',
          y, ' of type ', ('DIR' if ytype == b'\x01' else 'FILE'))

    # wait conflict decision from user
    print('Enter conflict decision:')
    cflDecision = chr(int(get_input(), 16))

    if cflDecision not in allowedUserDecs:
        print("Unknown conflict decision: ", ord(cflDecision))
        sys.exit(0)

    sock.sendall(cflDecision)

    if cflDecision == CD_REN_SRC or cflDecision == CD_REN_DEST:
        print('Please provide new filename:')
        newname = get_input()
        sendStringWithLen(sock,newname)

    commonTransition(sock)

def fromSKIP(sock):  # -> SIZE, EOFs, CFL, ERR
    global currentStatus
    outerProgressIncrement = struct.unpack("@Q", sock.recv(8))[0]
    totalSizeProgressIncrement = struct.unpack("@Q", sock.recv(8))[0]
    print('Outer progress increment on skip decision is', outerProgressIncrement)
    print('Total size progress increment on skip decision is', totalSizeProgressIncrement)
    commonTransition(sock)

def fromERR(sock): # -> SIZE or EOFs
    global currentStatus
    # receive involved paths
    x = receiveStringWithLen(sock)
    y = receiveStringWithLen(sock)

    xtype = sock.recv(1)
    ytype = sock.recv(1)

    print('Error paths are: ',
          x, ' of type ', ('DIR' if xtype == b'\x01' else 'FILE'), ' , ',
          y, ' of type ', ('DIR' if ytype == b'\x01' else 'FILE'))

    # wait error decision from user
    print('Enter error decision:')
    errDecision = chr(int(get_input(), 16))

    if errDecision not in allowedErrorDecs:
        print("Unknown error decision: ", ord(errDecision))
        sys.exit(0)

    if errDecision == ED_CANCEL:
        print("Exiting on user cancel")
        sys.exit(0)
    sock.sendall(errDecision)

    n = struct.unpack("@Q", sock.recv(8))[0]
    if n < 2 ** 64 - 5:  # SIZE
        print('Size is', n)
        # return fromSIZE(sock)
        currentStatus = SIZE
    else:
        # return transitionMap[n](sock) # EOFs
        if n != EOFs and n != SKIP:
            raise RuntimeError("Expected EOFs or SKIP here, protocol error")
        currentStatus = EOFs

def fromPROGRESS(sock): # -> PROGRESS,EOF,ERROR
    global currentStatus
    n = struct.unpack("@Q", sock.recv(8))[0]
    if n < 2 ** 64 - 5:  # another progress indication (SIZE is not allowed)
        print('Progress is', n)
        # return fromPROGRESS(sock)
        currentStatus = PROGRESS
    else:
        # return transitionMap[n](sock)
        currentStatus = n

def fromSIZE(sock): # -> PROGRESS,EOF,ERROR
    global currentStatus
    n = struct.unpack("@Q", sock.recv(8))[0]
    if n < 2 ** 64 - 5:  # another progress indication (SIZE is not allowed)
        print('Progress is ', n)
        # return fromPROGRESS(sock)
        currentStatus = PROGRESS
    else:
        # return transitionMap[n](sock)
        currentStatus = n

transitionMap = {
    EOF: fromEOF,
    EOFs: fromEOFs,
    CFL: fromCFL,
    ERR: fromERR,
    SIZE: fromSIZE,
    SKIP: fromSKIP,
    PROGRESS: fromPROGRESS
}

def fileCopyProgress(sock):
    global currentStatus
    global transitionMap
    currentStatus = SIZE
    while copyRunning:
        transitionMap[currentStatus](sock)
