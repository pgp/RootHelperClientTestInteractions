import struct
import sys
import os
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from net_common import *
from standalone_xre.xre_common import receiveStringWithLen
import sys


def remote_client_url_download(url="https://v.gd",
                               downloadDir='/dev/shm',
                               targetFilename='',
                               unixSocketNameWithoutTrailingNull='anotherRoothelper'):
    sock = get_connected_local_socket(unixSocketNameWithoutTrailingNull)

    rq = bytearray([ord(b'\x18') ^ (3 << 5)])  # ACTION_HTTPS_URL_DOWNLOAD request, flags: 011 (MSB: unused, httpsOnly: true, download to file: true)
    sock.sendall(rq)

    # send string-with-length of IP
    bUrl = bytearray(url.encode("utf-8"))
    sock.sendall(struct.pack("@H", len(bUrl)))
    sock.sendall(bUrl)
    # send download destination path
    bDestPath = bytearray(downloadDir.encode("utf-8"))
    sock.sendall(struct.pack("@H", len(bDestPath)))
    sock.sendall(bDestPath)
    # send target filename
    bTargetFilename = bytearray(targetFilename.encode("utf-8"))
    sock.sendall(struct.pack("@H", len(bTargetFilename)))
    if bTargetFilename: sock.sendall(bTargetFilename)

    # Server may perform more than one TLS handshake (due to 301/302 HTTP redirects), so send explicit EOF before sending download size
    while True:
        resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
        if resp != b'\x00':
            if resp == b'\x11':
                print('End of redirects')
                break
            print("Error byte received, errno is:", struct.unpack("@I", sock.recv(4))[0])
            return
        # receive TLS shared session secret hash (64-byte hex encoded SHA256)
        print("TLS master secret hash is:", toHex(sock.recv(32)))

    print("Received filename: ", receiveStringWithLen(sock))
    print("Download size is:", struct.unpack("@Q", sock.recv(8))[0])

    while True:
        p = struct.unpack("@Q", sock.recv(8))[0]
        if p == 2 ** 64 - 1:
            break
        print("Progress:", p)
    print("Completed")

    return sock

# replicate request with curl:
# curl -O -L --http1.0 https://api.github.com/repos/pgp/XFiles/releases
# curl -O -L --http1.0 https://api.github.com/repos/openssl/openssl/tags

if __name__ == '__main__':
    # rclient = remote_client_url_download(url="v.gd") # mandatory SNI
    # rclient = remote_client_url_download(url="fancyssl.hboeck.de") # TLS 1.2 only
    # rclient = remote_client_url_download(url="download-installer.cdn.mozilla.net/pub/firefox/releases/66.0.3/win64/it/Firefox%20Setup%2066.0.3.exe", targetFilename='ff.exe')
    rclient = remote_client_url_download(url="u.nu",targetFilename='unu.html')
    # rclient = remote_client_url_download(url="u.nu/fftest") # HTTP 301
    # rclient = remote_client_url_download(url="api.github.com/repos/openssl/openssl/tags", targetFilename='openssl_tags.json')
    # rclient = remote_client_url_download(url="www.cloudflare.com",targetFilename='www_cloudflare.html')
    if rclient is None:
        sys.exit(-1)
    rclient.close()
