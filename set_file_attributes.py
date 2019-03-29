from net_common import *
import struct

def send_filepath(_sock, b_file_path):
    _sock.sendall(struct.pack("=H", len(b_file_path)))  # len of path as unsigned short
    _sock.sendall(b_file_path)

def set_dates(_sock, b_file_path, access_timestamp=None, modification_timestamp=None):
    sub_rq_type = 0  # set_dates

    # dates flags
    flags = (0 if access_timestamp is None else 1) + \
            (0 if modification_timestamp is None else 2)
    print("flags:", flags)

    # additional_byte = chr((sub_rq_type << 6) + flags)  # python 2 only
    additional_byte = bytearray([(sub_rq_type << 6) + flags])

    _sock.sendall(additional_byte)
    send_filepath(_sock, b_file_path)

    # send dates
    if access_timestamp is not None:
        sock.sendall(struct.pack("@I", access_timestamp))
    if modification_timestamp is not None:
        sock.sendall(struct.pack("@I", modification_timestamp))

def set_ownership(_sock, b_file_path, owner_id=None, group_id=None):
    sub_rq_type = 1 # set_ownership

    # ownership flags
    flags = (0 if owner_id is None else 1) + \
            (0 if group_id is None else 2)

    # additional_byte = chr((sub_rq_type << 6) + flags)
    additional_byte = bytearray([(sub_rq_type << 6) + flags])
    _sock.sendall(additional_byte)
    send_filepath(_sock, b_file_path)

    # send ownerships
    if owner_id is not None:
        sock.sendall(struct.pack("@I",owner_id))
    if group_id is not None:
        sock.sendall(struct.pack("@I", group_id))

def set_permissions(_sock, _file_path, perm_mask):
    sub_rq_type = 2 # set_permissions

    # additional_byte = chr((sub_rq_type << 6))
    additional_byte = bytearray([(sub_rq_type << 6)])
    _sock.sendall(additional_byte)
    send_filepath(_sock, _file_path)

    # send permissions
    sock.sendall(struct.pack("@I", perm_mask))

if __name__ == '__main__':
    sock = get_connected_local_socket()

    rq = b'\x15'
    sock.sendall(rq)

    file_path_ = encodeString('/sdcard/fileio.bin')

    # set_dates(sock,
    #           file_path_,
    #           access_timestamp=2000000000,
    #           modification_timestamp=2100000000)

    # set_ownership(sock,
    #               file_path_,
    #               owner_id=1000,
    #               group_id=1000)

    set_permissions(sock,file_path_,intFromOctalString("0777"))

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received, errno:", struct.unpack("=i", sock.recv(4))[0])
