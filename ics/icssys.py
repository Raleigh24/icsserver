import argparse
import sys

import network
from rpcinterface import RPCProxy
from tabular import print_table
from ics_exceptions import ICSError

description_text = ''
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-loglevel', nargs=1, metavar='<level>', help='Set system log level')
parser.add_argument('-attr', action='store_true', help='list node attributes')
parser.add_argument('-value', nargs=1, metavar='<attr>',
                    help='print resource  attribute value')
parser.add_argument('-modify', nargs='+', #metavar=('<res>', '<attr>', '<value>'),
                    help='modify resource attribute')
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    exit()

try:
    conn = network.connect_udp()
except network.NetworkConnectionError:
    print('Unable to connect to ICS server')
    exit(1)

rpc_proxy = RPCProxy(conn)


def perform(func, *func_args):
    try:
        return func(*func_args)
    except ICSError as error:
        print('ERROR: ' + str(error))
        sys.exit(1)


if args.loglevel is not None:
    perform(rpc_proxy.set_log_level, args.loglevel)

elif args.attr:
    result = perform(rpc_proxy.node_attr)
    print_table(result)

elif args.value is not None:
    attr_name = args.value[0]
    result = perform(rpc_proxy.node_value, attr_name)
    print(result)

elif args.modify is not None:
    attr_name = args.modify[0]
    value = ' '.join(args.modify[1:])
    perform(rpc_proxy.node_modify, attr_name, value)

conn.close()
