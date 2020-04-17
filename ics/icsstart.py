import argparse
import socket

import Pyro4 as Pyro

from utils import setup_signal_handler
from utils import remote_execute

setup_signal_handler()
description_text = 'Start ICS server'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
args = parser.parse_args()

uri = 'PYRO:sub_server_control@' + socket.gethostname() + ':9091'
cluster = Pyro.Proxy(uri)
remote_execute(cluster.start)
