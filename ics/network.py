import select
import logging
import socket
import os

try:
    import queue
except ImportError:
    import Queue as queue  # Python2 version

try:
    import pickle
except ImportError:
    import cPickle as pickle  # Python2 version

from environment import ICS_UDS
from environment import ICS_UDS_FILE

logger = logging.getLogger(__name__)

HOST = ''
PORT = ''

clients = {}
recv_queue = queue.Queue()
poll = select.poll()


class NetworkError(Exception):
    """Exception is raised when there is a general network issue"""
    pass


class NetworkConnectionError(Exception):
    pass


class Client:
    def __init__(self, sock):
        self.sock = sock
        self.rest = bytes()
        self.sendQueue = queue.Queue()


def create_client(sock):
    return Client(sock)


def create_tcp_listen_socket(host, port):
    """Setup a TCP socket"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(100)
    return sock


def create_udp_listen_socket(filename):
    """ Setup the sockets the server will receive connection requests on """
    try:
        os.unlink(filename)
    except OSError as e:
        if os.path.exists(filename):
            logging.critical('Unable to create listening socket, ' + str(e))
            raise NetworkError

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.bind(filename)
    sock.listen(1)
    os.chmod(filename, 0o777)  # Change permissions to make writeable to everyone
    return sock


def connect_udp():
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(ICS_UDS_FILE)
        return sock
    except socket.error:
        raise NetworkConnectionError


def connect_tcp(host, port):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
    except socket.error:
        raise NetworkConnectionError


def parse_recvd_data(data):
    """ Break up raw received data into messages, delimited by null byte """
    parts = data.split(b'\0')
    msgs = parts[:-1]
    rest = parts[-1]
    return msgs, rest


def prep_msg(msg):
    msg += '\0'
    return msg


def send_msg(sock, msg):
    data = prep_msg(msg)
    sock.sendall(data)


def recv_msg(sock):
    data = bytearray()
    msg = ''
    while not msg:
        recvd = sock.recv(4096)
        if not recvd:
            raise socket.error

        #print 'recieved: ' + repr(recvd)
        data = data + recvd
        if b'\0' in recvd:
            msg = data.rstrip(b'\0')
    return msg


def recv_msgs(sock, data=bytes()):
    msgs = []
    while not msgs:
        recvd = sock.recv(4096)
        if not recvd:
            raise socket.error
        data = data + recvd
        (msgs, rest) = parse_recvd_data(data)
    return msgs, rest


def remote_cmd(sock, msg):
    pickled_msg = pickle.dumps(msg)
    send_msg(sock, pickled_msg)
    return_msg = recv_msg(sock)
    return pickle.loads(return_msg)


def send_client_msg(fd, msg):
    client = clients[fd]
    client.sendQueue.put(msg)
    poll.register(client.sock, select.POLLOUT)
    logger.debug('Queueing message to {} [{}]'.format(fd, repr(msg)))


def create_tcp_interface():
    """Create TCP interface and return socket"""
    try:
        listen_sock = create_tcp_listen_socket(HOST, PORT)
    except socket.error as error:
        logger.error('Failed to create listening socket: {}'.format(error))
        raise NetworkConnectionError
    return listen_sock


def create_udp_interface():
    """Create UDP interface and return socket"""
    if not os.path.isdir(ICS_UDS):
        logger.debug('UDS socket directory does not exist, will be created')
        try:
            os.makedirs(ICS_UDS)
        except Exception as e:
            logger.critical('Unable to create UDS socket directory, ' + str(e))
            raise NetworkError

    try:
        listen_sock = create_udp_listen_socket(ICS_UDS_FILE)
    except socket.error as error:
        logger.error('Failed to create listening socket: {}'.format(error))
        raise NetworkConnectionError
    return listen_sock


def handle_clients(listen_sock):
    poll.register(listen_sock, select.POLLIN)
    addr = listen_sock.getsockname()
    logger.debug('Listening on {}'.format(addr))

    while True:
        for fd, event in poll.poll(10):

            if event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                poll.unregister(fd)
                del clients[fd]

            elif fd == listen_sock.fileno():
                client_sock, addr = listen_sock.accept()
                client_sock.setblocking(False)
                fd = client_sock.fileno()
                clients[fd] = create_client(client_sock)
                poll.register(fd, select.POLLIN)
                logger.debug('Connection from {}'.format(addr))

            elif event & select.POLLIN:
                client = clients[fd]
                try:
                    addr = client.sock.getpeername()
                except socket.error:
                    logger.error('Unable to receive message, client no longer exists')
                    continue
                recvd = client.sock.recv(4096)
                if not recvd:
                    client.sock.close()
                    logger.debug('Client {} disconnected'.format(addr))
                    continue
                data = client.rest + recvd
                (msgs, client.rest) = parse_recvd_data(data)
                for msg in msgs:
                    recv_queue.put([fd, msg])

            elif event & select.POLLOUT:
                client = clients[fd]
                data = client.sendQueue.get()
                data_len = len(data)
                logger.debug('Sending message to {} [{}][{}]'.format(fd, data_len, repr(data)))
                send = client.sock.send(data + b'\0')
                # if send < len(data):
                #	client.sends.appendleft(data[sent:])
                if not client.sendQueue.empty():
                    poll.modify(client.sock, select.POLLOUT)
                else:
                    poll.modify(client.sock, select.POLLIN)

