import argparse
import sys
import socket
import time

import Pyro4 as Pyro

from environment import ICS_ENGINE_PORT
from environment import ICS_DAEMON_PORT
from ics_exceptions import ICSError
from tabular import print_table
from utils import setup_signal_handler

epilog_text = ''


def remote_execute(func, *func_args, **func_kwargs):
    """Wrapper for running commands remotely"""
    try:
        return func(*func_args, **func_kwargs)
    except ICSError as error:
        print('ERROR: ' + str(error))
        sys.exit(1)
    except Pyro.errors.CommunicationError as error:
        print('ERROR: Unable to connect to ICS server')
        print('ERROR: ' + str(error))
    except Exception:
        print('Pyro traceback:')
        print("".join(Pyro.util.getPyroTraceback()))


def daemon_conn():
    uri = 'PYRO:sub_server_control@' + socket.gethostname() + ':' + str(ICS_DAEMON_PORT)
    return Pyro.Proxy(uri)


def engine_conn():
    uri = 'PYRO:system@' + socket.gethostname() + ':' + str(ICS_ENGINE_PORT)
    return Pyro.Proxy(uri)


def icsd():
    pass


def icsstart():
    setup_signal_handler()
    description_text = 'Start ICS server'
    parser = argparse.ArgumentParser(description=description_text, epilog=epilog_text)
    args = parser.parse_args()
    cluster = daemon_conn()
    remote_execute(cluster.start)


def icsstop():
    setup_signal_handler()
    description_text = 'Stop ICS server'
    parser = argparse.ArgumentParser(description=description_text, epilog=epilog_text)
    parser.add_argument('-force', action='store_true', help="Force server to stop running")
    args = parser.parse_args()
    cluster = daemon_conn()
    remote_execute(cluster.stop, args.force)


def icssys():
    setup_signal_handler()
    description_text = 'Manage ICS system'
    parser = argparse.ArgumentParser(description=description_text, epilog=epilog_text, allow_abbrev=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-add', nargs=1, help='add a node to cluster')
    group.add_argument('-delete', nargs=1, help='delete a node from the cluster')
    group.add_argument('-loglevel', nargs=1, metavar='<level>', help='Set system log level')
    group.add_argument('-attr', action='store_true', help='list node attributes')
    group.add_argument('-value', nargs=1, metavar='<attr>', help='print resource  attribute value')
    group.add_argument('-modify', nargs=argparse.REMAINDER, metavar=('<res>', '<attr>', '<value>'),
                       help='modify resource attribute')
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    cluster = engine_conn()

    if args.add is not None:
        remote_execute(cluster.add_node, args.add[0])

    elif args.delete is not None:
        remote_execute(cluster.delete_node, args.delete[0])

    elif args.loglevel is not None:
        remote_execute(cluster.set_log_level, args.loglevel[0])

    elif args.attr:
        result = remote_execute(cluster.node_attr)
        print_table(result)

    elif args.value is not None:
        attr_name = args.value[0]
        result = remote_execute(cluster.node_value, attr_name)
        print(result)

    elif args.modify is not None:
        attr_name = args.modify[0]
        value = ' '.join(args.modify[1:])
        remote_execute(cluster.node_modify, attr_name, value)


def icsgrp():
    setup_signal_handler()
    description_text = 'Manage ICS service groups'
    parser = argparse.ArgumentParser(description=description_text, epilog=epilog_text, allow_abbrev=False)
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

    cluster = engine_conn()

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
        if len(group_list) == 0:
            results = remote_execute(cluster.clus_grp_state_all)
            print_table(results)
        elif len(group_list) == 1:
            group_name = group_list[0]
            group_state = remote_execute(cluster.clus_grp_state, group_name)
            print(group_state)
        else:
            results = remote_execute(cluster.clus_grp_state_all, group_names=group_list)
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


def icsres():
    setup_signal_handler()
    description_text = 'Manage ICS resources'
    parser = argparse.ArgumentParser(description=description_text, epilog=epilog_text, allow_abbrev=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-online', nargs=2, metavar=('<res>', '<system>'), help='bring resource online')
    group.add_argument('-offline', nargs=2, metavar=('<res>', '<system>'), help='bring resource offline')
    group.add_argument('-add', nargs=2, metavar=('<res>', '<group>'), help='add new resource')
    group.add_argument('-delete', nargs=1, metavar='<res>', help='delete existing resource')
    group.add_argument('-state', nargs='*', metavar='<res>', help='print current state of resource')
    group.add_argument('-link', nargs=2, metavar=('<parent>', '<child>'),
                       help='create dependency link between two resources')
    group.add_argument('-unlink', nargs=2, metavar=('<parent>', '<child>'),
                       help='remove dependency link between two resources')
    group.add_argument('-clear', nargs=1, metavar='<res>', help='remove fault status')
    group.add_argument('-probe', nargs=1, metavar='<res>', help='probe a resource')
    group.add_argument('-dep', nargs='*', metavar='<res>', help='print dependencies')
    group.add_argument('-list', action='store_true', help='print list of all resources')
    group.add_argument('-attr', nargs=1, metavar='<res>', help='print resource attributes')
    group.add_argument('-value', nargs=2, metavar=('<res>', '<attr>'), help='print resource  attribute value')
    group.add_argument('-modify', nargs=argparse.REMAINDER, metavar=('<res>', '<attr>', '<value>'),
                       help='modify resource attribute')
    group.add_argument('-wait', nargs=3, metavar=('<res>', '<state>', '<timeout>'),
                       help='wait for resource to change state')

    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit()

    cluster = engine_conn()

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


def icsalert():
    setup_signal_handler()
    description_text = 'Manage ICS alerts'
    parser = argparse.ArgumentParser(description=description_text, epilog=epilog_text, allow_abbrev=False)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-level', nargs=1, metavar='<level>', help='Set system log level')
    # group.add_argument('-test', action='store_true', help='') TODO: add test option and functionality
    group.add_argument('-add', nargs=1, help='add mail recipient')
    group.add_argument('-remove', nargs=1, help='remove mail recipient')
    args = parser.parse_args()

    if len(sys.argv) <= 1:
        parser.print_help()
        sys.exit(1)

    cluster = engine_conn()

    if args.level is not None:
        remote_execute(cluster.set_level, args.level[0])
    # elif args.test:
    #    pass
    elif args.add is not None:
        remote_execute(cluster.add_recipient, args.add[0])
    elif args.remove is not None:
        remote_execute(cluster.remove_recipient, args.remove[0])
