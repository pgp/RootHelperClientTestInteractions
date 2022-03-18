import struct
import sys
import os
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from net_common import *
from standalone_xre.xre_common import receiveStringWithLen
import sys


def remote_client_url_download(serverHost="v.gd",
                               serverPort=443,
                               unixSocketNameWithoutTrailingNull='anotherRoothelper'):
    sock = get_connected_local_socket(unixSocketNameWithoutTrailingNull)

    # ACTION_HTTPS_URL_DOWNLOAD request
    rq = bytearray([ord(b'\x18') ^ (2 << 5)])  # ACTION_HTTPS_URL_DOWNLOAD request, flags: 010 (MSB: unused, httpsOnly: true, download to file: false)
    sock.sendall(rq)

    # send string-with-length of IP
    bServerHost = bytearray(serverHost.encode("utf-8"))
    sock.sendall(struct.pack("@H", len(bServerHost)))
    sock.sendall(bServerHost)
    # send port
    sock.sendall(struct.pack("@H", serverPort))
    # send download destination path (WILL BE IGNORED)
    bDestPath = bytearray()
    sock.sendall(struct.pack("@H", len(bDestPath)))
    sock.sendall(bDestPath)
    # send target filename (WILL BE IGNORED)
    bTargetFilename = bytearray()
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
    with open('downloaded_content.bin', 'wb') as f:
        while True:
            chunk = sock.recv(1024)
            if chunk == b'':
                break
            f.write(chunk)

    return sock

# replicate request with curl:
# curl -O -L --http1.0 https://api.github.com/repos/pgp/XFiles/releases
# curl -O -L --http1.0 https://api.github.com/repos/openssl/openssl/tags

if __name__ == '__main__':
    rclient = remote_client_url_download(serverHost="v.gd") # mandatory SNI
    # rclient = remote_client_url_download(serverHost="fancyssl.hboeck.de",serverPort=443) # TLS 1.2 only
    # rclient = remote_client_url_download(serverHost="u.nu",serverPort=443)
    # rclient = remote_client_url_download(serverHost="www.cloudflare.com",serverPort=443)
    if rclient is None:
        sys.exit(-1)
    rclient.close()
