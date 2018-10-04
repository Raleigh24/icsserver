import argparse
import sys

import network
from rpcinterface import RPCProxy
from ics_exceptions import DoesNotExist

description_text = ''
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-loglevel', help='Set system log level')
parser.add_argument('-value', nargs=1, metavar=('<attr>'),
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

if args.loglevel is not None:
    result = rpc_proxy.set_log_level(args.loglevel)

elif args.value is not None:
    attr = args.value[0]
    try:
        result = rpc_proxy.node_value(attr)
        print(result)
    except DoesNotExist as error:
        print('ERROR: ' + str(error))
        sys.exit(1)
    except KeyError:
        print('ERROR: Attribute does not exists')
        sys.exit(1)

elif args.modify is not None:
    attr = args.modify[0]
    value = ' '.join(args.modify[1:])
    result = rpc_proxy.node_modify(attr, value)
    if not result:
        print('ERROR: Attribute does not exists')
        sys.exit(1)



conn.close()
