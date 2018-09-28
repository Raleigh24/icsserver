import argparse
import sys
import network
from rpcinterface import RPCProxy


description_text = ''
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-loglevel', help='')

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

if args.loglevel is not None:
    #print(args.loglevel)
    result = rpc_proxy.set_log_level(args.loglevel)

conn.close()
