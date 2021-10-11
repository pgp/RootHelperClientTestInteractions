from net_common import *
import struct
import sys

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def find_names(basePath,namePattern,find_in_subfolders,case_insensitive_name):
    print("**************Begin search**************")
    print(bcolors.OKBLUE)
    print("Base path: ", basePath)
    print("Name pattern: ", namePattern)
    print("Recursive search is ",
          bcolors.OKGREEN + "on" + bcolors.ENDC if find_in_subfolders is True else bcolors.FAIL + "off" + bcolors.ENDC)
    print(bcolors.OKBLUE + "Case insensitivity for names is ",
          bcolors.OKGREEN + "on" + bcolors.ENDC if case_insensitive_name is True else bcolors.FAIL + "off" + bcolors.ENDC)
    print(bcolors.ENDC)
    sock = get_connected_local_socket()

    rq = b'\x0B'

    if find_in_subfolders is True:
        rq = bytearray([ord(rq) ^ (0 << 5)]) # 000 include subfolders
    else:
        rq = bytearray([ord(rq) ^ (2 << 5)])  # 010 exclude subfolders

    # add search options flags
    if case_insensitive_name is True:
        searchFlags = bytearray([ord(b'\x00') ^ 4, 0])  # case insensitive name search
    else:
        searchFlags = bytearray([0,0])  # default, name search with case sensitivity

    sock.sendall(rq)
    sock.sendall(searchFlags)

    sock.sendall(struct.pack("=H", len(basePath)))
    sock.sendall(basePath)
    sock.sendall(struct.pack("=H", len(namePattern)))
    sock.sendall(namePattern)
    sock.sendall(struct.pack("=H", 0))  # no content pattern, no content search

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    print('response byte: ', ord(resp))
    if resp != b'\x00':
        print("Error byte received: ", struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)

    while True:
        filename_len = struct.unpack("=H", sock.recv(2))[0]
        if filename_len == 0: break  # end of list indication
        filename = sock.recv(filename_len).decode('utf-8')
        print("Filename:", filename)
        content_len = struct.unpack("=B", sock.recv(1))[0]
        if content_len != 0:
            print("Content:", sock.recv(content_len).decode('utf-8'))
            print("Offset:", struct.unpack("=Q", sock.recv(8))[0])
    print("**************End of search**************")
    sock.close()

class ls_resp_t:
    filename = ''
    date = 0  # 32 bit
    permissions = '----------'
    size = 0  # 64 bit
    # def __init__(self,filename,date,permissions,size):
    #     self.filename = filename
    #     self.date = date
    #     self.permissions = permissions
    #     self.size = size

class find_resp_t:
    lsresp = None
    contentAround = b''
    offset = 0
    # def __init__(self,lsresp,contentAround,offset):
    #     self.lsresp = lsresp
    #     self.contentAround = contentAround
    #     self.offset = offset

def find_names_with_ls_resp_t(basePaths: list,namePattern,find_in_subfolders,case_insensitive_name):
    print("**************Begin search**************")
    print(bcolors.OKBLUE)
    print("Base paths: ", basePaths)
    print("Name pattern: ", namePattern)
    print("Recursive search is ",
          bcolors.OKGREEN + "on" + bcolors.ENDC if find_in_subfolders is True else bcolors.FAIL + "off" + bcolors.ENDC)
    print(bcolors.OKBLUE + "Case insensitivity for names is ",
          bcolors.OKGREEN + "on" + bcolors.ENDC if case_insensitive_name is True else bcolors.FAIL + "off" + bcolors.ENDC)
    print(bcolors.ENDC)
    sock = get_connected_local_socket()

    rq = b'\x0B'

    if find_in_subfolders is True:
        rq = bytearray([ord(rq) ^ (0 << 5)]) # 000 include subfolders
    else:
        rq = bytearray([ord(rq) ^ (2 << 5)])  # 010 exclude subfolders

    # add search options flags
    if case_insensitive_name is True:
        searchFlags = bytearray([ord('\x00') ^ 4, 0])  # case insensitive name search
    else:
        searchFlags = bytearray([0,0])  # default, name search with case sensitivity

    sock.sendall(rq)
    sock.sendall(searchFlags)

    namePattern = encodeString(namePattern)
    for basePath in basePaths:
        basePath = encodeString(basePath)
        sock.sendall(struct.pack("=H", len(basePath)))
        sock.sendall(basePath)
    sock.sendall(struct.pack("=H", 0)) # EOL indication for basePaths
    sock.sendall(struct.pack("=H", len(namePattern)))
    sock.sendall(namePattern)
    sock.sendall(struct.pack("=H", 0))  # no content pattern, no content search

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    print('response byte: ', ord(resp))
    if resp != b'\x00':
        print("Error byte received, errno: ", struct.unpack("=i", sock.recv(4))[0])
        sys.exit(0)

    while True:
        entry = find_resp_t()
        entry.lsresp = ls_resp_t()
        filename_len = struct.unpack("=H", sock.recv(2))[0]
        if filename_len == 0: break  # end of list indication
        entry.lsresp.filename = sock.recv(filename_len).decode('utf-8')
        entry.lsresp.date = struct.unpack("=I", sock.recv(4))[0]
        entry.lsresp.permissions = sock.recv(10).decode('utf-8')
        entry.lsresp.size = struct.unpack("=Q", sock.recv(8))[0]

        print("Filename: ", entry.lsresp.filename,
              "Date: ", entry.lsresp.date,
              "Perms: ", entry.lsresp.permissions,
              "Size: ", entry.lsresp.size)

        content_len = struct.unpack("=B", sock.recv(1))[0]
        if content_len != 0:
            entry.contentAround = sock.recv(content_len)
            print("Content: ", toHex(entry.contentAround))
            entry.offset = struct.unpack("=Q", sock.recv(8))[0]
            print("Offset: ", entry.offset)
    print("**************End of search**************")
    sock.close()


if __name__ == "__main__":
    # ci_name_pattern = 'zIp'
    # cs_name_pattern = 'zip'
    
    base_paths = ['/sdcard/sf', '/sdcard/abc']
    ci_name_pattern = 'def'

    # find_names_with_ls_resp_t(base_paths,ci_name_pattern,True,True) # recursive, case-ins
    # find_names_with_ls_resp_t(base_paths,ci_name_pattern,False,True) # plain, case-ins

    # find_names_with_ls_resp_t(base_paths, ci_name_pattern, True, False)  # recursive, case-sens
    # find_names_with_ls_resp_t(base_paths, ci_name_pattern, False, False)  # plain, case-sens
    
    find_names_with_ls_resp_t(base_paths, ci_name_pattern, True, False)
