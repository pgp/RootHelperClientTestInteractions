import sys
import os
if not ('..' in sys.path or os.path.realpath('..') in sys.path): sys.path.append(os.path.realpath('..'))
from net_common import *
from standalone_xre.xre_common import sendStringWithLen

import struct

def remote_server(start=True):
	sock = get_connected_local_socket()

	start_server_rq = bytearray([ord(b'\x12') ^ (7 << 5)])
	start_server_with_announce_rq = bytearray([ord(b'\x12') ^ (5 << 5)])
	stop_server_rq = bytearray([ord(b'\x12') ^ (0 << 5)])
	get_server_status_rq = bytearray([ord(b'\x12') ^ (2 << 5)])

	sock.sendall(start_server_with_announce_rq if start else stop_server_rq)

	# OLD PROTOCOL (rh version < 1.2)
	# sock.sendall(bytearray([0]))  # don't restrict access to a custom directory

	# NEW PROTOCOL, send default, announced and exposed path on start
	sendStringWithLen(sock, b'')  # default path (send empty for leaving unchanged)
	sendStringWithLen(sock, b'')  # announced path (enabling announce depends on start flags)
	sendStringWithLen(sock, b'')  # exposed path (send empty for no restrictions)

	resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
	if resp != b'\x00':
		print("Error byte received, errno:", struct.unpack("@I", sock.recv(4))[0])
		return

	while True:
		# receive one byte as boolean (0x00, connected or 0xFF, disconnected)
		# receive string with length containing IP and ephemeral port of client
		resp = sock.recv(1)
		#length
		l = struct.unpack("@B", sock.recv(1))[0]
		clientIPandPort = sock.recv(l)

		if resp == b'\x00':
			print("Client connected:", clientIPandPort)
			# receive TLS shared session secret hash (32-byte SHA256)
			print('TLS master secret hash is:', toHex(sock.recv(32)))
		else:
			print("Client disconnected:", clientIPandPort)


if __name__ == "__main__":
	remote_server(True)
	# remote_server(False)

