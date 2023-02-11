from net_common import *
from standalone_xre.xre_common import sendStringWithLen, receiveStringWithLen
import struct

CREATE_FILE_RQ_BYTE = bytearray([ord(b'\x09') ^ (1 << 5)])
CREATE_FILE_ADV_RQ_BYTE = bytearray([ord(b'\x09') ^ (3 << 5)]) # create file with advanced options (flags 011)
CREATE_DIR_RQ_BYTE = bytearray([ord(b'\x09') ^ (0 << 5)])

# server giving permission denied if run from within CLion
if __name__ == "__main__":
    sock = get_connected_local_socket()

    file_path = encodeString("/dev/shm/randfile1") # fallocate won't always work on tmpfs /dev/shm
    fmode = struct.pack("=I", intFromOctalString("0644"))

    #  send create request for given file
    # rq = CREATE_FILE_RQ_BYTE
    # rq = CREATE_DIR_RQ_BYTE
    rq = CREATE_FILE_ADV_RQ_BYTE

    print("rq is",ord(rq))

    sock.sendall(rq)
    sock.sendall(struct.pack("=H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)
    sock.sendall(fmode)

    # creation strategy: 0 fallocate (not supported by Android API 19, disabled), 1 zeros, 2 random, plus two flag bits

    # creationStrategy = 0 # b'\x00' # fallocate
    # creationStrategy = 1 # b'\x01' # zeros
    creationStrategy = 2   # b'\x02' # random

    creationStrategy |= 4  # supply custom seed for initializing PRNG
    creationStrategy |= 8  # request hash output for generated file

    sock.sendall(creationStrategy.to_bytes(1)) # byte order is not necessary here, since we are only packing a single byte

    sock.sendall(struct.pack("=Q", 2 ** 30))  # send size - 1 GB file
    # sock.sendall(struct.pack("=Q", 0)) # 0 b (empty) file

    # send seed if the corresponding flag is enabled
    if creationStrategy & 2:
        if creationStrategy & 4:
            prngSeed = 'customSeed1234'
            print(f'Supplying custom seed for PRNG init: {prngSeed}')
            sendStringWithLen(sock, prngSeed)
        # send hash type for output hash, if the corresponding flag is enabled
        if creationStrategy & 8:
            targetHash = 'sha224'
            print(f'Requesting output hash {targetHash} for generated file')
            sendStringWithLen(sock, targetHash)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received, errno:",struct.unpack("=i", sock.recv(4))[0])
    else:
        if rq == CREATE_FILE_ADV_RQ_BYTE:
            # receive progress
            while True:
                currentProgress = struct.unpack("@Q", sock.recv(8))[0]
                print(f"Progress: {currentProgress}")
                if currentProgress == 2 ** 64 - 1:
                    print("End of progress")
                    break
            if creationStrategy & 2 and creationStrategy & 8:  # (& 2) && (& 8), since the two flag bits are ignored if not creating a random file
                output_hash = receiveStringWithLen(sock).decode('utf-8')
                print(f'{targetHash} for the generated file is: {output_hash}')
    sock.close()
