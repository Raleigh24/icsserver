import socket

uds_address = '/var/opt/ics/net/uds_socket'

class ConnectionError(Exception):
    pass


def create_uds_socket():
    """ Setup the unix domain socket """
    try:
        os.unlink(uds_address)
    except OSError:
        if os.path.exists(uds_address):
            raise

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(uds_address)
    return sock


def connect_uds():
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(uds_address)
        return sock
    except socket.error:
        raise ConnectionError


def create_uds_interface():
    try:
        uds_sock = create_uds_socket()
    except socket.error as e:
        logger.error('Failed to create UDS socket: {}'.format(e))
        raise ConnectionError
    return uds_sock

