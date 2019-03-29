from net_common import *


def send_exit_request():
    sock = get_connected_local_socket()
    rq = b'\x1F'
    sock.sendall(rq)

if __name__ == "__main__":
    send_exit_request()
