import argparse
import sys
import socket
import time

import Pyro4 as Pyro

from tabular import print_table
from utils import setup_signal_handler
from utils import remote_execute

setup_signal_handler()
description_text = 'Manage ICS resources'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text, allow_abbrev=False)
parser.add_argument('-online', nargs=2, metavar=('<res>', '<system>'),
                    help='bring resource online')
parser.add_argument('-offline', nargs=2, metavar=('<res>', '<system>'),
                    help='bring resource offline')
parser.add_argument('-add', nargs=2, metavar=('<res>', '<group>'),
                    help='add new resoruce')
parser.add_argument('-delete', nargs=1, metavar='<res>',
                    help='delete existing resource')
parser.add_argument('-state', nargs='*', metavar='<res>',
                    help='print current state of resource')
parser.add_argument('-link', nargs=2, metavar=('<parent>', '<child>'),
                    help='create dependancy link between two resources')
parser.add_argument('-unlink', nargs=2, metavar=('<parent>', '<child>'),
                    help='remove dependancy link between two resources')
parser.add_argument('-clear', nargs=1, metavar='<res>',
                    help='remove fault status')
parser.add_argument('-probe', nargs=1, metavar='<res>',
                    help='probe a resource')
parser.add_argument('-dep', nargs='*', metavar='<res>',
                    help='print dependencies')
parser.add_argument('-list', action='store_true',
                    help='print list of all resources')
parser.add_argument('-attr', nargs=1, metavar='<res>',
                    help='print resource attributes')
parser.add_argument('-value', nargs=2, metavar=('<res>', '<attr>'),
                    help='print resource  attribute value')
parser.add_argument('-modify', nargs=argparse.REMAINDER, metavar=('<res>', '<attr>', '<value>'),
                    help='modify resource attribute')
parser.add_argument('-wait', nargs=3, metavar=('<res>', '<state>', '<timeout>'),
                    help='wait for resource to change state')

args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit()


uri = 'PYRO:system@' + socket.gethostname() + ':9090'
cluster = Pyro.Proxy(uri)

if args.online is not None:
    resource_name = args.online[0]
    system_name = args.online[1]
    remote_execute(cluster.clus_res_online, resource_name, system_name)

elif args.offline is not None:
    resource_name = args.offline[0]
    system_name = args.offline[1]
    remote_execute(cluster.clus_res_offline, resource_name, system_name)

elif args.add is not None:
    resource_name = args.add[0]
    group_name = args.add[1]
    remote_execute(cluster.clus_res_add, resource_name, group_name)

elif args.delete is not None:
    resource_name = args.delete[0]
    remote_execute(cluster.clus_res_delete, resource_name)

elif args.state is not None:
    resource_list = args.state
    if len(resource_list) == 1:
        resource_name = resource_list[0]
        resource_state = remote_execute(cluster.clus_res_state, resource_name)
        print(resource_state)
        #results = [[resource_name, resource_state]]
    else:
        results = remote_execute(cluster.clus_res_state_many, resource_list, include_node=True)
        print_table(results)

elif args.link is not None:
    parent_name = args.link[0]
    child_name = args.link[1]
    remote_execute(cluster.clus_res_link, parent_name, child_name)

elif args.unlink is not None:
    parent_name = args.unlink[0]
    child_name = args.unlink[1]
    remote_execute(cluster.clus_res_unlink, parent_name, child_name)

elif args.clear is not None:
    resource_name = args.clear[0]
    remote_execute(cluster.clus_res_clear, resource_name)

elif args.probe is not None:
    resource_name = args.probe[0]
    remote_execute(cluster.clus_res_probe, resource_name)

elif args.dep is not None:
    results = remote_execute(cluster.clus_res_dep, args.dep)
    header = ['Group', 'Parent', 'Child']
    print_table(results, header=header, col_sort=0)

elif args.list is True:
    resources = remote_execute(cluster.clus_res_list)
    for resource in resources:
        print(resource)

elif args.attr is not None:
    resource_name = args.attr[0]
    result = remote_execute(cluster.clus_res_attr, resource_name)
    print_table(result)

elif args.value is not None:
    resource_name = args.value[0]
    attr_name = args.value[1]
    result = remote_execute(cluster.clus_res_value, resource_name, attr_name)
    print(result)

elif args.modify is not None:
    resource_name = args.modify[0]
    attr = args.modify[1]
    value = ' '.join(args.modify[2:])
    remote_execute(cluster.clus_res_modify, resource_name, attr, value)

elif args.wait is not None:
    resource_name, state_name, timeout = args.wait

    try:
        timer = int(timeout)
    except ValueError:
        print('ERROR: Timeout parameter not in correct format')
        sys.exit(1)

    while timer != 0:
        if remote_execute(cluster.clus_res_state, [resource_name])[0][0] == state_name:
            sys.exit(0)  # Exit with return code 0 when state value matches
        time.sleep(1)
        timer -= 1
    sys.exit(1)  # Exit with return code 1 when timeout is reached

else:
    parser.print_help()
