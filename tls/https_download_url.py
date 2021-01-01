import struct
import sys
import os
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from net_common import *
from standalone_xre.xre_common import receiveStringWithLen
import sys


def remote_client_url_download(serverHost="v.gd",
                               serverPort=443,
                               downloadDir='/dev/shm',
                               targetFilename='',
                               unixSocketNameWithoutTrailingNull='anotherRoothelper'):
    sock = get_connected_local_socket(unixSocketNameWithoutTrailingNull)

    rq = bytearray(b'\x18')  # ACTION_HTTPS_URL_DOWNLOAD request
    sock.sendall(rq)

    # send string-with-length of IP
    bServerHost = bytearray(serverHost.encode("utf-8"))
    sock.sendall(struct.pack("@H", len(bServerHost)))
    sock.sendall(bServerHost)
    # send port
    sock.sendall(struct.pack("@H", serverPort))
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


if __name__ == '__main__':
    # rclient = remote_client_url_download(serverHost="v.gd") # mandatory SNI
    # rclient = remote_client_url_download(serverHost="fancyssl.hboeck.de",serverPort=443) # TLS 1.2 only
    # rclient = remote_client_url_download(serverHost="download-installer.cdn.mozilla.net/pub/firefox/releases/66.0.3/win64/it/Firefox%20Setup%2066.0.3.exe", targetFilename='ff.exe')
    rclient = remote_client_url_download(serverHost="u.nu",serverPort=443,targetFilename='unu.html')
    # rclient = remote_client_url_download(serverHost="u.nu/fftest") # HTTP 301
    # rclient = remote_client_url_download(serverHost="api.github.com/repos/openssl/openssl/tags", targetFilename='openssl_tags.json')
    # rclient = remote_client_url_download(serverHost="www.cloudflare.com",serverPort=443,targetFilename='www_cloudflare.html')
    if rclient is None:
        sys.exit(-1)
    rclient.close()
