import argparse
import sys
import socket

import Pyro4 as Pyro

from tabular import print_table
from utils import setup_signal_handler
from utils import remote_execute

setup_signal_handler()
description_text = 'Manage ICS system'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text, allow_abbrev=False)
parser.add_argument('-add', nargs=1, help='add a node to cluster')
parser.add_argument('-delete', nargs=1, help='delete a node from the cluster')
parser.add_argument('-loglevel', nargs=1, metavar='<level>', help='Set system log level')
parser.add_argument('-attr', action='store_true', help='list node attributes')
parser.add_argument('-value', nargs=1, metavar='<attr>', help='print resource  attribute value')
parser.add_argument('-modify', nargs=argparse.REMAINDER, metavar=('<res>', '<attr>', '<value>'),
                    help='modify resource attribute')
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit(1)

uri = 'PYRO:system@' + socket.gethostname() + ':9090'
cluster = Pyro.Proxy(uri)

if args.add is not None:
    remote_execute(cluster.add_node, args.add[0])

elif args.delete is not None:
    remote_execute(cluster.delete_node, args.delete[0])

elif args.loglevel is not None:
    remote_execute(cluster.set_log_level, args.loglevel[0])

elif args.attr:
    result = remote_execute(cluster.node_attr)
    print_table(result)

elif args.value is not None:
    attr_name = args.value[0]
    result = remote_execute(cluster.node_value, attr_name)
    print(result)

elif args.modify is not None:
    attr_name = args.modify[0]
    value = ' '.join(args.modify[1:])
    remote_execute(cluster.node_modify, attr_name, value)
