import argparse
import sys
import network

from ics_exceptions import DoesNotExist, AlreadyExists
from rpcinterface import RPCProxy
from tabular import print_table
import utils

utils.setup_signal_handler()
description_text = ''
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-online', nargs=1, metavar=('<group>'),
                    help='bring group online')
parser.add_argument('-offline', nargs=1, metavar=('<group>'),
                    help='bring group offline')
parser.add_argument('-add', nargs=1, metavar=('<group>'),
                    help='add new resource')
parser.add_argument('-delete', nargs=1, metavar=('<group>'),
                    help='delete existing group')
parser.add_argument('-enable', nargs=1, metavar=('<group>'),
                    help='enable resources for a group')
parser.add_argument('-disable', nargs=1, metavar=('<group>'),
                    help='disable resources for a group')
parser.add_argument('-state', nargs='*', metavar=('<group>'),
                    help='print current state of resource')
parser.add_argument('-link', nargs=2, metavar=('<parent>', '<child>'),
                    help='create dependancy link between two resources')
parser.add_argument('-unlink', nargs=2, metavar=('<parent>', '<child>'),
                    help='remove dependancy link between two resources')
parser.add_argument('-clear', nargs=1, metavar=('<group>'),
                    help='remove fault status')
parser.add_argument('-flush', nargs=1, metavar=('<group>'),
                    help='')
parser.add_argument('-resources', nargs=1, metavar=('<group>'),
                    help='list all resources for a given group')
parser.add_argument('-list', action='store_true',
                    help='print list of all resources')
parser.add_argument('-attr', nargs=1, metavar=('<group>'),
                    help='print group attributes')
parser.add_argument('-value', nargs=2, metavar=('<res>', '<attr>'),
                    help='print group  attribute value')
parser.add_argument('-modify', nargs=3, metavar=('<group>', '<attr>', '<value>'),
                    help='modify resource attribute')
parser.add_argument('-wait', nargs=4, metavar=('<group>', '<attr>', '<value>', '<timeout>'),
                    help='wait for attribute to change to value')
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit()

try:
    conn = network.connect_udp()
except network.NetworkConnectionError:
    print('ERROR: Unable to connect to ICS server')
    sys.exit(1)

rpc_proxy = RPCProxy(conn)


def perform(func, *func_args):
    try:
        func(*func_args)
    except DoesNotExist as e:
        print('ERROR: ' + str(e))
        sys.exit(1)


if args.online is not None:
    group_name = args.online[0]
    perform(rpc_proxy.grp_online, group_name)

elif args.offline is not None:
    group_name = args.offline[0]
    perform(rpc_proxy.grp_offline, group_name)

elif args.add is not None:
    group_name = args.add[0]
    try:
        perform(rpc_proxy.grp_add, group_name)
    except AlreadyExists as e:
        print('ERROR: ' + str(e))

elif args.delete is not None:
    group_name = args.delete[0]
    perform(rpc_proxy.grp_delete, group_name)

elif args.enable is not None:
    group_name = args.enable[0]
    perform(rpc_proxy.grp_enable, group_name)

elif args.disable is not None:
    group_name = args.disable[0]
    perform(rpc_proxy.grp_disable, group_name)

elif args.state is not None:
    results = rpc_proxy.grp_state(args.state)
    print_table(results)

elif args.clear is not None:
    group_name = args.clear[0]
    perform(rpc_proxy.grp_clear, group_name)

elif args.flush is not None:
    group_name = args.flush[0]
    perform(rpc_proxy.grp_flush, group_name)

elif args.resources is not None:
    group_name = args.resources[0]
    result = rpc_proxy.grp_resources(group_name)
    for resource_name in result:
        print(resource_name)

elif args.list is True:
    groups = rpc_proxy.grp_list()
    for group_name in groups:
        print(group_name)

elif args.attr is not None:
    group_name = args.attr[0]
    result = rpc_proxy.grp_attr(group_name)
    print_table(result)

elif args.value is not None:
    group_name = args.value[0]
    attr = args.value[1]
    try:
        result = rpc_proxy.grp_value(group_name, attr)
        print(result)
    except DoesNotExist as error:
        print('ERROR: ' + str(error))
        sys.exit(1)
    except KeyError:
        print('Error: Attribute does not exists')
        sys.exit(1)

elif args.modify is not None:
    group_name = args.modify[0]
    attr = args.modify[1]
    value = ' '.join(args.modify[2:])
    result = rpc_proxy.grp_modify(group_name, attr, value)
    if not result:
        print('ERROR: Attribute does not exist')
        sys.exit(1)

else:
    parser.print_help()

conn.close()
