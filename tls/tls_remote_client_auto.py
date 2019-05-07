import struct
from datetime import datetime
import sys
if not '..' in sys.path: sys.path.append('..')
from net_common import *
import sys
import subprocess
from time import sleep

def create_file_or_dir(sock, path, mkdir=True):
	# rq = chr(ord('\x09') ^ ((0<<5) if mkdir else (1<<5))) # python 2 only
	rq = bytearray([ord(b'\x09') ^ ((0<<5) if mkdir else (1<<5))])
	sock.sendall(rq)
	bpath = encodeString(path)
	sock.sendall(struct.pack("=H", len(bpath)))  # len of path as unsigned short
	sock.sendall(bpath)
	fmode = struct.pack("=I", intFromOctalString("0755" if mkdir else "0644"))
	sock.sendall(fmode)
	resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
	if resp != b'\x00':
		print("Error byte received, errno:", struct.unpack("=i", sock.recv(4)))
		sys.exit(0)
	sock.close()


def list_dir(sock, path='/'):
	sock.sendall(bytearray(b'\x01'))  # LS request
	bpath = encodeString(path)
	sock.sendall(struct.pack("@H", len(bpath)))  # len of path as unsigned short
	sock.sendall(bpath)

	resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR

	if resp != b'\x00':
		print("Error byte received")
		sys.exit(-1)
	cnt = []
	while True:
		ll = struct.unpack("@H", sock.recv(2))[0]  # receive file entry (filename) length
		if ll == 0: break
		fname = sock.recv(ll).decode('utf-8') # receive file entry (filename)
		fdate = datetime.fromtimestamp(struct.unpack("@I", sock.recv(4))[0])
		fperms = sock.recv(10).decode('utf-8')
		fsize = struct.unpack("@Q", sock.recv(8))[0]

		cnt.append((fname, fdate, fperms, fsize))
		print(fname + '\t' + str(fdate) + '\t' + fperms + '\t' + str(fsize))


UPLOAD = False
DOWNLOAD = True
def upload_or_download_items(sock, downloadOrUpload, *pathpairs):
	rq_byte = b'\x10' if downloadOrUpload is DOWNLOAD else b'\x11'
	sock.sendall(rq_byte)
	for p in pathpairs:
		pathpair = (encodeString(p[0]), encodeString(p[1]))
		# send the two path lengths
		sock.sendall(struct.pack("@H",len(pathpair[0])))
		sock.sendall(struct.pack("@H", len(pathpair[1])))
		# send the two paths
		sock.sendall(pathpair[0])
		sock.sendall(pathpair[1])
	sock.sendall(bytearray([0,0,0,0])) # send end of list

	# read total number of files for updating external progress
	print("Total files:", struct.unpack("@Q", sock.recv(8))[0])
	currentFiles = 0

	# receive progresses
	hasReceivedSizeForcurrentFile = False  # set to false after an EOF, and at the beginning
	while True:
		currentProgress = struct.unpack("@Q", sock.recv(8))[0]
		if currentProgress == 2 ** 64 - 1:
			print("File completed")
			hasReceivedSizeForcurrentFile = False
			currentFiles += 1
		elif currentProgress == 2 ** 64 - 2:
			print("Received end of transfer")
			break
		else:
			# inner progress, print size or progress
			if hasReceivedSizeForcurrentFile:
				print("Current file:", currentFiles, "\tCurrent progress:", currentProgress)
			else:
				print("Current file:", currentFiles, "\tReceived file size:", currentProgress)
				hasReceivedSizeForcurrentFile = True


def remote_client(serverHost="192.168.43.1",serverPort=11111,socketName="rootHelper"):
	sock = get_connected_local_socket(socketName)

	rq = bytearray(b'\x14') # REMOTE_CONNECT request
	sock.sendall(rq)

	# send string-with-length of IP
	bServerHost = bytearray(serverHost.encode("utf-8"))
	sock.sendall(struct.pack("@B",len(bServerHost)))
	sock.sendall(bServerHost)
	# send port
	sock.sendall(struct.pack("@H",serverPort))

	resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
	if resp != b'\x00':
		print("Error byte received, errno is:", struct.unpack("@I", sock.recv(4))[0])
		return

	# receive TLS shared session secret hash (32-byte SHA256)
	print("TLS master secret hash is:", toHex(sock.recv(32)))

	return sock



if __name__ == "__main__":
	if len(sys.argv) != 5 or (sys.argv[1] != "UP" and sys.argv[1] != "DOWN"):
		print("Usage: ", sys.argv[0], """
UP <host> <srcLocalPath> <destRemotePath>
or
DOWN <host> <srcRemotePath> <destLocalPath>""")
		exit(0)
	rhUnixSocketName = "autoRH"
	workdir = "/media/pgp/Dati/p7zip_cust_ndk/XFilesRootHelper/bin/"
	rhlocal = subprocess.Popen([workdir+"r","1000",rhUnixSocketName],cwd=workdir)
	sleep(1)

	rclient = remote_client(serverHost=sys.argv[2], serverPort=11111, socketName=rhUnixSocketName)
	if rclient is None:
		sys.exit(-1)

	upload_or_download_items(rclient,
							 UPLOAD if sys.argv[1] == "UP" else DOWNLOAD,
							 (sys.argv[3],sys.argv[4]))

	rclient.close()
	rhlocal.kill()
