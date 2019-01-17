import argparse
import sys

import network
from rpcinterface import RPCProxy
from ics_exceptions import ICSError

description_text = 'Manage ICS alerts'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-level', nargs=1, metavar='<level>', help='Set system log level')
#parser.add_argument('-test', action='store_true', help='') TODO: add test option and functionality
parser.add_argument('-add', nargs=1, help='add mail recipient')
parser.add_argument('-remove', nargs=1, help='remove mail recipient')
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit(1)

try:
    conn = network.connect_udp()
except network.NetworkConnectionError:
    print('Unable to connect to ICS server')
    sys.exit(1)

rpc_proxy = RPCProxy(conn)


def perform(func, *func_args):
    try:
        return func(*func_args)
    except ICSError as error:
        print('ERROR: ' + str(error))
        sys.exit(1)


if args.level is not None:
    perform(rpc_proxy.set_level, args.level[0])
elif args.test:
    pass
elif args.add is not None:
    perform(rpc_proxy.add_recipient, args.add[0])
elif args.remove is not None:
    perform(rpc_proxy.remove_recipient, args.remove[0])

conn.close()
