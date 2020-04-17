import argparse
import socket

import Pyro4 as Pyro

from utils import setup_signal_handler
from utils import remote_execute

setup_signal_handler()
description_text = 'Stop ICS server'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-force', action='store_true', help="Force server to stop running")
args = parser.parse_args()

uri = 'PYRO:sub_server_control@' + socket.gethostname() + ':9091'
cluster = Pyro.Proxy(uri)
remote_execute(cluster.stop, args.force)
