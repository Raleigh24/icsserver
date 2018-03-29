import argparse
import sys
import network
from rpcinterface import RPCProxy


description_text = ''
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-makerw', action='store_true', help='')
parser.add_argument('-makero', action='store_true', help='')
parser.add_argument('-save', action='store_true', help='')
parser.add_argument('-reload', action='store_true', help=())

args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    exit()

try:
    conn = network.connect('', 4040)
except network.ConnectionError:
    print('Unable to connect to ICS server')
    exit(1)

rpc_proxy = RPCProxy(conn)


if args.makerw:
    pass

elif args.makero:
    pass

elif args.save:
    pass
elif args.reload:
    pass
else:
    parser.print_help()

conn.close()
