from __future__ import print_function
import ssl
import pprint
import sys
import os
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
if not ('.' in sys.path or os.path.realpath('.') in sys.path): sys.path.append(os.path.realpath('.'))
from net_common import *
from xre_common import *

"""
TLS client example, using python's native openssl bindings.
Should work on both python 2 and 3, and both openssl 1.0 and 1.1
"""

UPLOAD = False
DOWNLOAD = True


def upload_items(sock, *pathpairs):
	descendantCountMap = vdict()
	counts = [0, 0, 0]

	for pathpair in pathpairs:
		itemTotals = countTotalStatsIntoMap(pathpair[0], descendantCountMap)
		counts[0] += itemTotals[0]
		counts[1] += itemTotals[1]
		counts[2] += itemTotals[2]

	rq_byte = b'\x11'
	sock.sendall(rq_byte)
	sock.sendall(struct.pack("@Q", counts[0]))  # tFiles
	sock.sendall(struct.pack("@Q", counts[2]))  # tSize
	l = []
	l.extend(pathpairs)
	while l:
		p = l.pop()
		if os.path.isdir(p[0]):
			l.extend((os.path.join(p[0],child), pathConcat(p[1],child, detectSep=True)) for child in os.listdir(p[0]))
		ItemWithContent(p[0], p[1]).write(sock)  # send dir info (flag byte and pathname)
	ItemWithContent.eol(sock) # send end of list

def download_items(sock, *pathpairs):
	rq_byte = b'\x10'
	sock.sendall(rq_byte)
	# TODO

if __name__ == '__main__':
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

	# Require a certificate from the server. We used a self-signed certificate
	# so here ca_certs must be the server certificate itself.
	tls_sock = ssl.wrap_socket(s,
							   ca_certs="dummycrt.pem",
							   cert_reqs=ssl.CERT_REQUIRED)

	tls_sock.connect(('10.0.2.2', 11111))

	print(repr(tls_sock.getpeername()))
	print(tls_sock.cipher())
	print(pprint.pformat(tls_sock.getpeercert()))

	upload_items(tls_sock, ("/sdcard/testfolder_1", "C:\\sdcard\\tf2"))
	# upload_items(tls_sock, UPLOAD, ("/C:/sdcard/1.bin", "/C:/Temp/2.bin"))

