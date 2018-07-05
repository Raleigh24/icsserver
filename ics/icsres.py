import argparse
import sys

import network
from resource import DoesNotExist, AlreadyExists
from rpcinterface import RPCProxy
from tabular import print_table
import utilities


utilities.setup_signal_handler()
description_text = ''
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text)
parser.add_argument('-online', nargs=1, metavar=('<res>'),
                    help='bring resource online')
parser.add_argument('-offline', nargs=1, metavar=('<res>'),
                    help='bring resource offline')
parser.add_argument('-add', nargs=2, metavar=('<res>', '<group>'),
                    help='add new resoruce')
parser.add_argument('-delete', nargs=1, metavar=('<res>'),
                    help='delete existing resource')
parser.add_argument('-state', nargs='*', metavar=('<res>'),
                    help='print current state of resource')
parser.add_argument('-link', nargs=2, metavar=('<parent>', '<child>'),
                    help='create dependancy link between two resources')
parser.add_argument('-unlink', nargs=2, metavar=('<parent>', '<child>'),
                    help='remove dependancy link between two resources')
parser.add_argument('-clear', nargs=1, metavar=('<res>'),
                    help='remove fault status')
parser.add_argument('-probe', nargs=1, metavar=('<res>'),
                    help='probe a resource')
parser.add_argument('-dep', nargs='*', metavar=('<res>'),
                    help='print dependencies')
parser.add_argument('-list', action='store_true',
                    help='print list of all resources')
parser.add_argument('-value', nargs=2, metavar=('<res>', '<attr>'),
                    help='print resource  attribute value')
parser.add_argument('-modify', nargs='+', #metavar=('<res>', '<attr>', '<value>'),
                    help='modify resource attribute')
parser.add_argument('-wait', nargs=4, metavar=('<res>', '<attr>', '<value>', '<timeout>'),
                    help='wait for attribute to change to value')

args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    exit()

try:
    conn = network.connect('', 4040)
except network.NetworkConnectionError:
    print('ERROR: Unable to connect to ICS server')
    exit(1)

rpc_proxy = RPCProxy(conn)


def perform(func, *func_args):
    try:
        return func(*func_args)
    except DoesNotExist as e:
        print('ERROR: ' + str(e))
        exit(1)


if args.online is not None:
    resource_name = args.online[0]
    perform(rpc_proxy.res_online, resource_name)

elif args.offline is not None:
    resource_name = args.offline[0]
    perform(rpc_proxy.res_offline, resource_name)

elif args.add is not None:
    resource_name = args.add[0]
    group_name = args.add[1]
    try:
        perform(rpc_proxy.res_add, resource_name, group_name)
    except AlreadyExists as e:
        print('ERROR: ' + str(e))

elif args.delete is not None:
    resource_name = args.delete[0]
    perform(rpc_proxy.res_delete, resource_name)

elif args.state is not None:
    #results = rpc_proxy.state(args.state)
    results = perform(rpc_proxy.res_state, args.state)
    print_table(results)


elif args.link is not None:
    parent_name = args.link[0]
    child_name = args.link[1]
    perform(rpc_proxy.res_link, parent_name, child_name)
    # TODO: handle exception when link exists or not in same group

elif args.unlink is not None:
    parent_name = args.unlink[0]
    child_name = args.unlink[1]
    rpc_proxy.res_unlink(parent_name, child_name)

elif args.clear is not None:
    resource_name = args.clear[0]
    perform(rpc_proxy.res_clear, resource_name)

elif args.probe is not None:
    resource_name = args.probe[0]
    perform(rpc_proxy.res_probe, resource_name)

elif args.dep is not None:
    results = rpc_proxy.res_dep(args.dep)
    header = ['Group', 'Parent', 'Child']
    print_table(results, header=header, col_sort=0)

elif args.list is True:
    resources = rpc_proxy.res_list()
    for resource in resources:
        print(resource)

elif args.value is not None:
    resource_name = args.value[0]
    value = args.value[1]
    try:
        result = rpc_proxy.res_value(resource_name, value)
    except DoesNotExist as e:
        print('ERROR: ' + str(e))
    except KeyError:
        print('ERROR: Attribute does not exists')
        exit(1)

    print(result)

elif args.modify is not None:
    resource_name = args.modify[0]
    value = args.modify[1]
    attr = ' '.join(args.modify[2:])
    result = rpc_proxy.res_modify(resource_name, value, attr)
    if not result:
        print('ERROR: Attribute does not exists')
        exit(1)

elif args.wait is not None:
    resource_name = args.wait[0]
    attr_name = args.wait[1]
    value_name = args.wait[2]
    timeout = args.wait[3]

else:
    parser.print_help()

conn.close()





















