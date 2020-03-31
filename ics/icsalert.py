import argparse
import sys
import socket

import Pyro4 as Pyro

from utils import setup_signal_handler
from utils import remote_execute

setup_signal_handler()
description_text = 'Manage ICS alerts'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text, allow_abbrev=False)
group = parser.add_mutually_exclusive_group()
group.add_argument('-level', nargs=1, metavar='<level>', help='Set system log level')
#group.add_argument('-test', action='store_true', help='') TODO: add test option and functionality
group.add_argument('-add', nargs=1, help='add mail recipient')
group.add_argument('-remove', nargs=1, help='remove mail recipient')
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit(1)

uri = 'PYRO:system@' + socket.gethostname() + ':9090'
system = Pyro.Proxy(uri)

if args.level is not None:
    remote_execute(system.set_level, args.level[0])
#elif args.test:
#    pass
elif args.add is not None:
    remote_execute(system.add_recipient, args.add[0])
elif args.remove is not None:
    remote_execute(system.remove_recipient, args.remove[0])
