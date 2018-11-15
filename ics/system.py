import logging
import os
import sys
import threading
import time

import network
from events import event_handler
from alerts import AlertHandler
from rpcinterface import rpc_runner
from ics_exceptions import ICSError
from utils import set_log_level, read_config, write_config
from environment import ICS_CONF_FILE

from attributes import AttributeObject, system_attributes
from states import ResourceStates, TRANSITION_STATES
from resource import Resource, Group

logger = logging.getLogger(__name__)


class NodeSystem(AttributeObject):

    def __init__(self):
        super(NodeSystem, self).__init__()
        self.init_attr(system_attributes)
        self.node_name = ""
        self.cluster_name = ""

        self.threads = []
        self.alert_handler = AlertHandler()

        self.resources = {}
        self.groups = {}

    def set_attr(self, attr, value):
        if attr == "ClusterName":
            pass
        elif attr == "NodeName":
            pass

        super(NodeSystem, self).set_attr(attr, value)

    def node_attr(self):
        """Return a list of node attributes"""
        return self.attr_list()

    def node_value(self, attr_name):
        """Return node attribute"""
        return self.attr_value(attr_name)

    def node_modify(self, attr_name, value):
        """Modify a node attribute"""
        try:
            self.set_attr(attr_name, value)
        except KeyError:
            return False
        return True

    def get_resource(self, resource_name):
        """Get resource object from resources list"""
        if resource_name in self.resources.keys():
            resource = self.resources[resource_name]
            return resource
        else:
            raise ICSError('Resource {} does not exist'.format(resource_name))

    def res_online(self, resource_name):
        """Interface for bringing resource online"""
        resource = self.get_resource(resource_name)
        if resource.attr_value('MonitorOnly') == 'true':
            raise ICSError('Unable to online resource, MonitoryOnly mode enabled')
        if resource.state is not ResourceStates.ONLINE:
            resource.change_state(ResourceStates.STARTING)

    def res_offline(self, resource_name):
        """Interface for bringing resource offline"""
        resource = self.get_resource(resource_name)
        if resource.attr_value('MonitorOnly') == 'true':
            raise ICSError('Unable to offline resource, MonitoryOnly mode enabled')
        if resource.state is not ResourceStates.OFFLINE:
            resource.change_state(ResourceStates.STOPPING)

    def res_add(self, resource_name, group_name):
        """Interface for adding new resource"""
        logger.info('Adding new resource {}'.format(group_name))
        if resource_name in self.resources.keys():
            raise ICSError('Resource {} already exists'.format(resource_name))
        elif group_name not in self.groups.keys():
            raise ICSError('Group {} does not exist'.format(group_name))
        elif len(self.resources) >= int(self.attr_value('ResourceLimit')):
            raise ICSError('Max resource count reached, unable to add new resource')
        else:
            resource = Resource(resource_name, group_name)
            self.resources[resource_name] = resource
            group = self.groups[group_name]
            group.add_resource(resource)
            return resource

    def res_delete(self, resource_name):
        """Interface for deleting existing resource"""
        resource = self.get_resource(resource_name)

        for parent in resource.parents:
            parent.children.remove(resource)

        for child in resource.children:
            child.parents.remove(resource)

        group = self.get_group(resource.attr_value('Group'))
        group.delete_resource(resource)
        del self.resources[resource_name]
        logger.info('Resource({}) resource deleted'.format(resource_name))

    def res_state(self, resource_args):
        """Interface for getting resource current state """
        resource_states = []
        if len(resource_args) == 1:
            resource = self.get_resource(resource_args[0])
            resource_states.append([resource.state.upper()])
        elif resource_args:
            for resource_name in resource_args:
                resource = self.get_resource(resource_name)
                resource_states.append([resource.name, resource.state.upper()])
        else:
            for resource in self.resources.values():
                resource_states.append([resource.name, resource.state.upper()])

        return resource_states

    def res_link(self, parent_name, resource_name):
        """Interface to link two resources"""
        resource = self.get_resource(resource_name)
        parent_resource = self.get_resource(parent_name)
        if resource.attr_value('Group') != parent_resource.attr_value('Group'):
            raise ICSError('Unable to add link, resources not in same group')
        resource.add_parent(parent_resource)
        parent_resource.add_child(resource)
        logger.info('Resource({}) created dependency on {}'.format(resource_name, parent_name))

    def res_unlink(self, parent_name, resource_name):
        """Interface to unlink two resources"""
        resource = self.get_resource(resource_name)
        parent_resource = self.get_resource(parent_name)
        resource.remove_parent(parent_name)
        parent_resource.remove_child(resource)

    def res_clear(self, resource_name):
        """Interface for clearing resource in a faulted state"""
        resource = self.get_resource(resource_name)
        resource.clear()

    def res_probe(self, resource_name):
        """Interface for manually triggering a poll"""
        resource = self.get_resource(resource_name)
        resource.probe()

    def res_dep(self, resource_args):
        """Interface for getting resource dependencies"""
        dep_list = []
        if len(resource_args) == 0:
            for resource in self.resources.values():
                resource_group_name = resource.attr_value('Group')
                for parent in resource.parents:
                    row = [resource_group_name, parent.name, resource.name]
                    dep_list.append(row)
        else:
            for resource_name in resource_args:
                resource = self.get_resource(resource_name)
                resource_group_name = resource.attr_value('Group')
                for parent in resource.parents:
                    row = [resource_group_name, parent.name, resource.name]
                    dep_list.append(row)
                for child in resource.children:
                    row = [resource_group_name, resource.name, child.name]
                    dep_list.append(row)

        return dep_list

    def res_list(self):
        """Interface for listing all resources"""
        return self.resources.keys()

    def res_value(self, resource_name, attr_name):
        """Interface for getting attribute value for resource"""
        resource = self.get_resource(resource_name)
        return resource.attr_value(attr_name)

    def res_modify(self, resource_name, attr_name, value):
        """Interface for modifying attribute for resource"""
        resource = self.get_resource(resource_name)
        try:
            resource.set_attr(attr_name, value)
        except KeyError:
            return False
        return True

    def res_attr(self, resource_name):
        """Interface for getting resource attributes"""
        resource = self.get_resource(resource_name)
        return resource.attr_list()

    def get_group(self, group_name):
        """Get group object from groups list"""
        if group_name in self.groups.keys():
            group = self.groups[group_name]
            return group
        else:
            raise ICSError('Group {} does not exist'.format(group_name))

    def grp_online(self, group_name):
        """Interface for bringing a group online"""
        logger.info('Group({}) bringing online'.format(group_name))
        group = self.get_group(group_name)
        group.start()

    def grp_online_auto(self):
        """Auto start service groups which have the AutoStart attribute enabled"""
        for group in self.groups.values():
            if group.attr_value('AutoStart') == 'true':
                group.start()

    def grp_offline(self, group_name):
        """Interface for bringing a group offline"""
        logger.info('Group({}) bringing offline'.format(group_name))
        group = self.get_group(group_name)
        group.stop()

    def grp_state(self, group_args):
        """Interface for getting state of group"""
        group_states = []
        if len(group_args) == 1:
            group = self.get_group(group_args[0])
            group_states.append([group.state().upper()])
        elif group_args:
            for group_name in group_args:
                group = self.get_group(group_name)
                group_states.append([group.name, group.state().upper()])
        else:
            for group in self.groups.values():
                group_states.append([group.name, group.state().upper()])

        return group_states

    def grp_add(self, group_name):
        """Interface for adding a new group"""
        logger.info('Adding new group {}'.format(group_name))
        if group_name in self.groups.keys():
            ICSError('Group {} already exists'.format(group_name))
        elif len(self.groups) >= int(self.attr_value('GroupLimit')):
            raise ICSError('Max group count reached, unable to add new group')
        else:
            group = Group(group_name)
            self.groups[group_name] = group
            return group

    def grp_delete(self, group_name):
        """Interface for deleting an existing group"""
        logger.info('Deleting group {}'.format(group_name))
        group = self.get_group(group_name)
        if not group.members:
            del self.groups[group_name]
        else:
            logger.error('Unable to delete group ({}), group still contains resources'.format(group_name))
            pass  # delete object?

    def grp_enable(self, group_name):
        """Interface to enable a group"""
        group = self.get_group(group_name)
        group.set_attr('Enabled', 'true')

    def grp_disable(self, group_name):
        """Interface to disable a group"""
        group = self.get_group(group_name)
        group.set_attr('Enabled', 'false')

    def grp_enable_resources(self, group_name):
        """Interface to enable a group resources """
        group = self.get_group(group_name)
        group.enable_resources()

    def grp_disable_resources(self, group_name):
        """Interface to disable a group resources"""
        group = self.get_group(group_name)
        group.disable_resources()

    def grp_flush(self, group_name):
        """Interface for flushing a group"""
        group = self.get_group(group_name)
        group.flush()

    def grp_clear(self, group_name):
        """Interface for clearing a group"""
        group = self.get_group(group_name)
        group.clear()

    def grp_resources(self, group_name):
        """Interface for getting members of a group"""
        group = self.get_group(group_name)
        resource_names = []
        for member in group.members:
            resource_names.append(member.name)
        return resource_names

    def grp_list(self):
        """Interface for listing all existing group names"""
        return self.groups.keys()

    def grp_value(self, group_name, attr_name):
        """Return an attribute for a given group and attribute"""
        group = self.get_group(group_name)
        return group.attr[attr_name]

    def grp_modify(self, group_name, attr_name, value):
        """Modify an attribute for a given group"""
        group = self.get_group(group_name)
        try:
            group.set_attr(attr_name, value)
        except KeyError:
            return False
        return True

    def grp_attr(self, group_name):
        """Return a list of attributes for a given group"""
        group = self.get_group(group_name)
        return group.attr_list()

    def poll_updater(self):  # TODO: rename function
        """Continuously check for resources ready for poll"""
        while True:
            for resource in self.resources.values():
                if resource.attr_value('Enabled') == 'false':
                    continue
                elif resource.cmd_process is not None:
                    if resource.check_cmd():
                        resource.handle_cmd()
                elif resource.state in TRANSITION_STATES:
                    continue
                else:
                    resource.update_poll()
            time.sleep(1)

    def start_threads(self):
        # Start event handler thread
        logger.info('Starting event handler...')
        thread_event_handler = threading.Thread(name='event handler', target=event_handler)
        thread_event_handler.daemon = True
        thread_event_handler.start()
        self.threads.append(thread_event_handler)

        # Start alert handler thread
        logger.info('Starting alert handler...')
        thread_alert_handler = threading.Thread(name='alert handler', target=self.alert_handler.run)
        thread_alert_handler.daemon = True
        thread_alert_handler.start()
        self.threads.append(thread_alert_handler)

        # Start client handler thread
        logger.info('Starting client handler...')
        try:
            sock = network.create_udp_interface()
        except network.NetworkError:
            logger.critical('Unable to create client interface, exiting...')
            raise ICSError
        thread_client_handler = threading.Thread(name='client handler', target=network.handle_clients, args=(sock,))
        thread_client_handler.daemon = True
        thread_client_handler.start()
        self.threads.append(thread_client_handler)

        # Start poll updater thread
        logger.info('Starting poll updater...')
        thread_poll_updater = threading.Thread(name='poll updater', target=self.poll_updater)
        thread_poll_updater.daemon = True
        thread_poll_updater.start()
        self.threads.append(thread_poll_updater)

        # Start config backup
        logger.info('Starting auto backups...')
        thread_config_backup = threading.Thread(name='backup config', target=self.backup_config)
        thread_config_backup.daemon = True
        thread_config_backup.start()
        self.threads.append(thread_config_backup)

        # Function list to be registered with rpc interface
        rpc_function_list = [
            set_log_level,
            self.node_attr,
            self.node_value,
            self.node_modify,
            self.res_online,
            self.res_offline,
            self.res_add,
            self.res_delete,
            self.res_state,
            self.res_clear,
            self.res_probe,
            self.res_dep,
            self.res_list,
            self.res_link,
            self.res_unlink,
            self.res_value,
            self.res_modify,
            self.res_attr,
            self.grp_online,
            self.grp_offline,
            self.grp_add,
            self.grp_delete,
            self.grp_enable,
            self.grp_disable,
            self.grp_enable_resources,
            self.grp_disable_resources,
            self.grp_state,
            self.grp_flush,
            self.grp_clear,
            self.grp_resources,
            self.grp_list,
            self.grp_value,
            self.grp_modify,
            self.grp_attr,
            self.alert_handler.add_recipient,
            self.alert_handler.remove_recipient,
            self.alert_handler.set_level
        ]

        # Start RPC interface thread
        logger.info('Starting RPC interface...')
        thread_rpc_interface = threading.Thread(name='RPC interface', target=rpc_runner, args=(rpc_function_list,))
        thread_rpc_interface.daemon = True
        thread_rpc_interface.start()
        self.threads.append(thread_rpc_interface)

    def config_data(self):
        """Return system configuration data in dictionary format"""
        config_data = {
            'system': {'attributes': self.modified_attributes()},
            'alerts': {'attributes': {
                'AlertLevel': self.alert_handler.get_level(), 'AlertRecipients': self.alert_handler.recipients},
            },
            'groups': {},
            'resources': {}
        }

        for group in self.groups.values():
            config_data['groups'][group.name] = {'attributes': group.modified_attributes()}
        for resource in self.resources.values():
            config_data['resources'][resource.name] = {'attributes': resource.modified_attributes(),
                                                       'dependencies': resource.dependencies()}
        return config_data

    def load_config(self, data):
        logger.info('Loading configuration...')

        try:
            # Set system attributes from config
            system_data = data['system']
            for attr_name in system_data['attributes']:
                self.set_attr(attr_name, system_data['attributes'][attr_name])

            # Set alert attributes from config
            alert_data = data['alerts']
            self.alert_handler.set_level(alert_data['attributes']['AlertLevel'])
            for recipient in alert_data['attributes']['AlertRecipients']:
                self.alert_handler.add_recipient(recipient)

            # Create groups from config
            group_data = data['groups']
            for group_name in group_data:
                group = self.grp_add(group_name)
                for attr_name in group_data[group_name]['attributes']:
                    group.set_attr(attr_name, str(group_data[group_name]['attributes'][attr_name]))

            # Create resources from config
            resource_data = data['resources']
            for resource_name in resource_data.keys():
                group_name = resource_data[resource_name]['attributes']['Group']
                resource = self.res_add(resource_name, group_name)
                for attr_name in resource_data[resource_name]['attributes']:
                    resource.set_attr(attr_name, str(resource_data[resource_name]['attributes'][attr_name]))

            # Create resource dependency links
            # Note: Links need to be done in separate loop to guarantee parent resources
            # are created first when establishing links
            for resource_name in resource_data.keys():
                for dep_name in resource_data[resource_name]['dependencies']:
                    self.res_link(dep_name, resource_name)
        except (TypeError, KeyError) as error:
            logging.error('Error occurred while loading config: {}:{}'.format(error.__class__.__name__, str(error)))
            raise

    def backup_config(self):
        while True:
            interval = int(self.attr_value('BackupInterval'))
            if interval != 0:
                logging.debug('Creating backup of config file')
                if os.path.isfile(ICS_CONF_FILE):
                    os.rename(ICS_CONF_FILE, ICS_CONF_FILE + '.autobackup')
                write_config(ICS_CONF_FILE, self.config_data())
                time.sleep(interval * 60)
            else:
                time.sleep(60)

    def startup(self):
        logger.info('Server starting up...')
        # TODO: Add config startup management here

        data = read_config(ICS_CONF_FILE)
        if data:
            try:
                self.load_config(data)
            except Exception as e:
                logging.critical('Error reading config data: {}'.format(str(e)))
                #TODO: send alert
                sys.exit(1)  # TODO: better system handling
        else:
            logger.info('No configuration data found')

        self.start_threads()
        self.grp_online_auto()
        # TODO: start polling updater
        logger.info('Server startup complete')

    def run(self):
        while True:
            for thread in self.threads:
                if not thread.is_alive():
                    logger.critical('Thread {} no longer running'.format(thread.name))
            time.sleep(5)

    def shutdown(self):
        logging.info('Server shutting down...')
        write_config(ICS_CONF_FILE, self.config_data())
        logging.info('Server shutdown complete')
        logging.shutdown()
