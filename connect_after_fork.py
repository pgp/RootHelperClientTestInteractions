from net_common import *

if __name__ == "__main__":
    sock = get_connected_local_socket("anotherRoothelper")
    rq = b'\x00'
    sock.sendall(rq)

    resp = sock.recv(1)  # response first byte: \x00 OK or \xFF ERROR
    if resp != b'\x00':
        print("Error byte received")
    else:
        print("OK response received")
    sock.close()

