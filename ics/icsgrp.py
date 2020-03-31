import argparse
import sys
import socket
import time

import Pyro4 as Pyro

from tabular import print_table
from utils import setup_signal_handler
from utils import remote_execute


setup_signal_handler()
description_text = 'Manage ICS service groups'
epilog_text = ''
parser = argparse.ArgumentParser(description=description_text, allow_abbrev=False)
group = parser.add_mutually_exclusive_group()
group.add_argument('-online', nargs=2, metavar=('<group>', '<system>'), help='bring group online')
group.add_argument('-offline', nargs=2, metavar=('<group>', '<system>'), help='bring group offline')
group.add_argument('-add', nargs=1, metavar='<group>', help='add new resource')
group.add_argument('-delete', nargs=1, metavar='<group>', help='delete existing group')
group.add_argument('-enable', nargs=1, metavar='<group>', help='enable resources for a group')
group.add_argument('-disable', nargs=1, metavar='<group>', help='disable resources for a group')
group.add_argument('-enableresources', nargs=1, metavar='<group>', help='enable all resources for a group')
group.add_argument('-disableresources', nargs=1, metavar='<group>', help='disable all resources for a group')
group.add_argument('-state', nargs='*', metavar='<group>', help='print current state of resource')
group.add_argument('-link', nargs=2, metavar=('<parent>', '<child>'),
                   help='create dependancy link between two resources')
group.add_argument('-unlink', nargs=2, metavar=('<parent>', '<child>'),
                   help='remove dependancy link between two resources')
group.add_argument('-clear', nargs=2, metavar=('<group>', '<system>'), help='remove fault status')
group.add_argument('-flush', nargs=2, metavar=('<group>', '<system>'), help='flush resource')
group.add_argument('-resources', nargs=1, metavar='<group>', help='list all resources for a given group')
group.add_argument('-list', action='store_true', help='print list of all resources')
group.add_argument('-attr', nargs=1, metavar='<group>', help='print group attributes')
group.add_argument('-value', nargs=2, metavar=('<res>', '<attr>'), help='print group  attribute value')
group.add_argument('-modify', nargs=argparse.REMAINDER, metavar=('<group>', '<attr>', '<value>'),
                   help='modify resource attribute')
group.add_argument('-wait', nargs=3, metavar=('<group>', '<state>', '<timeout>'),
                   help='wait for resource to change state')
args = parser.parse_args()

if len(sys.argv) <= 1:
    parser.print_help()
    sys.exit()

uri = 'PYRO:system@' + socket.gethostname() + ':9090'
cluster = Pyro.Proxy(uri)

if args.online is not None:
    group_name = args.online[0]
    system_name = args.online[1]
    remote_execute(cluster.clus_grp_online, group_name, system_name)

elif args.offline is not None:
    group_name = args.offline[0]
    system_name = args.offline[1]
    remote_execute(cluster.clus_grp_offline, group_name, system_name)

elif args.add is not None:
    group_name = args.add[0]
    remote_execute(cluster.clus_grp_add, group_name)

elif args.delete is not None:
    group_name = args.delete[0]
    remote_execute(cluster.clus_grp_delete, group_name)

elif args.enable is not None:
    group_name = args.enable[0]
    remote_execute(cluster.clus_grp_enable, group_name)

elif args.disable is not None:
    group_name = args.disable[0]
    remote_execute(cluster.clus_grp_disable, group_name)

elif args.enableresources is not None:
    group_name = args.enableresources[0]
    remote_execute(cluster.clus_grp_enable_resources, group_name)

elif args.disableresources is not None:
    group_name = args.disableresources[0]
    remote_execute(cluster.clus_grp_disable_resources, group_name)

elif args.state is not None:
    group_list = args.state  # List of provided group names
    if len(group_list) == 1:
        group_name = group_list[0]
        group_state = remote_execute(cluster.clus_grp_state, group_name)
        print(group_state)
    else:
        results = remote_execute(cluster.clus_grp_state_many, group_list, include_node=True)
        print_table(results)

elif args.clear is not None:
    group_name = args.clear[0]
    system_name = args.clear[1]
    remote_execute(cluster.clus_grp_clear, group_name, system_name)

elif args.flush is not None:
    group_name = args.flush[0]
    system_name = args.flush[1]
    remote_execute(cluster.clus_grp_flush, group_name, system_name)

elif args.resources is not None:
    group_name = args.resources[0]
    result = remote_execute(cluster.clus_grp_resources, group_name)
    for group_name in result:
        print(group_name)

elif args.list is True:
    groups = cluster.clus_grp_list()
    for group_name in groups:
        print(group_name)

elif args.attr is not None:
    group_name = args.attr[0]
    result = remote_execute(cluster.clus_grp_attr, group_name)
    print_table(result)

elif args.value is not None:
    group_name = args.value[0]
    attr = args.value[1]
    result = remote_execute(cluster.clus_grp_value, group_name, attr)
    print(result)

elif args.modify is not None:
    group_name = args.modify[0]
    attr = args.modify[1]
    value = ' '.join(args.modify[2:])
    remote_execute(cluster.clus_grp_modify, group_name, attr, value)

elif args.wait is not None:
    group_name, state_name, timeout = args.wait
    try:
        timer = int(timeout)
    except ValueError:
        print('ERROR: Timeout parameter not in correct format')
        sys.exit(1)

    while timer != 0:
        if remote_execute(cluster.clus_grp_state, [group_name])[0][0] == state_name:
            sys.exit(0)  # Exit with return code 0 when state value matches
        time.sleep(1)
        timer -= 1
    sys.exit(1)  # Exit with return code 1 when timeout is reached

else:
    parser.print_help()
