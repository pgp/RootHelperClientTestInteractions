from net_common import *
import struct
import sys

if __name__ == "__main__":
    sock = get_connected_local_socket()

    origin = bytearray('/sdcard/BIGFILES_TEST/test_strcmp'.encode('utf-8'))
    # origin = '/sdcard/BIGFILES_TEST/test_strcmp_0' # no occurrences present
    expr = bytearray('theexpr'.encode('utf-8'))

    sock.sendall(bytearray(b'\x0B'))  # FIND_IN_CONTENT request
    sock.sendall(struct.pack("=H", len(origin)))  # len of path as unsigned short
    sock.sendall(struct.pack("=H", len(expr)))  # len of path as unsigned short
    sock.sendall(origin)
    sock.sendall(expr)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    print('response byte:', ord(resp))
    if resp != b'\x00':
        print('Error byte received, errno:',struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)
    
    # receive number of occurrences as 64-bit signed integer
    occurrences = struct.unpack("=q", sock.recv(8))[0]

    if occurrences < 0:
        print("Negative return value:",occurrences)
    elif occurrences == 0:
        print("No occurrences found")
    else:
        print(occurrences,"occurrences found")
        for _ in range(occurrences):
            # read offset as unsigned 64-bit integer
            offset = struct.unpack("=Q", sock.recv(8))[0]
            print("Offset:",offset)
