import sys
if not '..' in sys.path: sys.path.append('..')
from net_common import *

import struct

def remote_server(start=True):
	sock = get_connected_local_socket()

	# start_server_rq = chr(ord('\x12') ^ (7 << 5))
	# stop_server_rq = chr(ord('\x12') ^ (0 << 5))
	# get_server_status_rq = chr(ord('\x12') ^ (2 << 5))
	start_server_rq = bytearray([ord(b'\x12') ^ (7 << 5)])
	stop_server_rq = bytearray([ord(b'\x12') ^ (0 << 5)])
	get_server_status_rq = bytearray([ord(b'\x12') ^ (2 << 5)])

	sock.sendall(start_server_rq if start else stop_server_rq)

	sock.sendall(bytearray([0])) # don't restrict access to a custom directory

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

		if resp == '\x00':
			print("Client connected:", clientIPandPort)
			# receive TLS shared session secret hash (64-byte hex encoded SHA256)
			print('TLS master secret hash is:', toHex(sock.recv(64)))
		else:
			print("Client disconnected:", clientIPandPort)


if __name__ == "__main__":
	remote_server(True)
	# remote_server(False)

