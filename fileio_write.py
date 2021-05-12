from net_common import *
import struct
import sys
import requests

if __name__ == "__main__":
    sock = get_connected_local_socket()

    rq = b'\x0F' # flags: 000

    file_path = encodeString('/sdcard/fileio.bin')

    sock.sendall(rq)  # FILEIO request
    sock.sendall(struct.pack("=H", len(file_path)))  # len of path as unsigned short
    sock.sendall(file_path)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

    if resp != b'\x00':
        print("Error byte received,errno:",struct.unpack("=i", sock.recv(4)))
        sys.exit(0)

    url = 'https://rarlab.com/rar/winrar-x64-570.exe'
    file_name = url.split('/')[-1]
    r = requests.get(url,allow_redirects=True,stream=True)
    r.raise_for_status()
    try:
        file_size = int(r.headers["Content-Length"])
        print("Downloading: %s Bytes: %s" % (file_name, file_size))
    except:
        print("File size not available")
        file_size = None

    file_size_dl = 0
    latest_shown_size = 0
    block_sz = 8192
    # outfile = open(file_path,'wb')
    for chunk in r.iter_content(chunk_size=block_sz):
        if chunk:
            file_size_dl += len(chunk)
            sock.sendall(chunk)
            # outfile.write(chunk)
            if file_size_dl - latest_shown_size > 500000:
                latest_shown_size = file_size_dl
                if file_size is not None:
                    status = "Downloaded: " + str(file_size_dl) + " (" + str(file_size_dl * 100.0 / file_size) + " %)"
                else:
                    status = "Downloaded (bytes): " + str(file_size_dl)
                print(status)

    sock.close()

