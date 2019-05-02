import struct
import sys
if not '..' in sys.path: sys.path.append('..')
from net_common import *
import sys


def remote_client_url_download(serverHost="v.gd",serverPort=443, downloadPath='/dev/shm/ciao.bin', unixSocketNameWithoutTrailingNull='anotherRoothelper'):
	sock = get_connected_local_socket(unixSocketNameWithoutTrailingNull)

	rq = bytearray(b'\x18') # ACTION_HTTPS_URL_DOWNLOAD request
	sock.sendall(rq)

	# send string-with-length of IP
	bServerHost = bytearray(serverHost.encode("utf-8"))
	sock.sendall(struct.pack("@H",len(bServerHost)))
	sock.sendall(bServerHost)
	# send port
	sock.sendall(struct.pack("@H",serverPort))
	# send download destination path
	bDestPath = bytearray(downloadPath.encode("utf-8"))
	sock.sendall(struct.pack("@H", len(bDestPath)))
	sock.sendall(bDestPath)

	resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
	if resp != b'\x00':
		print("Error byte received, errno is:", struct.unpack("@I", sock.recv(4))[0])
		return

	# receive TLS shared session secret hash (64-byte hex encoded SHA256)
	print("TLS master secret hash is:", toHex(sock.recv(64)))
	print("Download size is:", struct.unpack("@Q", sock.recv(8))[0])

	while True:
		p = struct.unpack("@Q", sock.recv(8))[0]
		if p == 2**64-1:
			break
		print("Progress:",p)
	print("Completed")

	return sock


if __name__ == '__main__':
	# rclient = remote_client_url_download(serverHost="v.gd",serverPort=443,downloadPath='/dev/shm/xfileshttpclient.txt') # mandatory SNI
	# rclient = remote_client_url_download(serverHost="fancyssl.hboeck.de",serverPort=443,downloadPath='/dev/shm/urldownload.txt') # TLS 1.2 only
	# rclient = remote_client_url_download(serverHost="download-installer.cdn.mozilla.net/pub/firefox/releases/66.0.3/win64/it/Firefox%20Setup%2066.0.3.exe",serverPort=443,downloadPath='/dev/shm/ff.exe')
	# rclient = remote_client_url_download(serverHost="u.nu",serverPort=443,downloadPath='/dev/shm/unu.txt')
	rclient = remote_client_url_download(serverHost="cloudflare.com",serverPort=443) # HTTP 301
	# rclient = remote_client_url_download(serverHost="www.cloudflare.com",serverPort=443,downloadPath='/dev/shm/cloudflare.txt')
	if rclient is None:
		sys.exit(-1)
	rclient.close()
