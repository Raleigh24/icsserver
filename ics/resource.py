import logging
import random
import subprocess
import time
import os

import events
import alerts
from attributes import AttributeObject, system_attributes, resource_attributes, group_attributes
from ics_exceptions import ICSError
from utils import read_json, write_json
from environment import ICS_RES_LOG, ICS_CONF_FILE
from states import ResourceStates, GroupStates, ONLINE_STATES, TRANSITION_STATES

logger = logging.getLogger(__name__)


class Node(AttributeObject):

    def __init__(self):
        super(Node, self).__init__()
        self.init_attr(system_attributes)
        self.resources = {}
        self.groups = {}

    def set_attr(self, attr, value):
        if attr == "ClusterName":
            pass
        elif attr == "NodeName":
            pass

        super(Node, self).set_attr(attr, value)

    def poll_updater(self):
        """Continuously check for resources ready for poll"""
        while True:
            for resource in self.resources.values():
                if resource.attr_value('Enabled') == 'false':
                    logger.debug('Resource({}) is not enabled, skipping poll'.format(resource.name))
                    continue
                elif resource.cmd_process is not None:
                    if resource.check_cmd():
                        resource.handle_cmd()
                elif resource.state in TRANSITION_STATES:
                    continue
                else:
                    resource.update_poll()
            time.sleep(1)

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
            group_states.append([group.state.upper()])
        elif group_args:
            for group_name in group_args:
                group = self.get_group(group_name)
                group_states.append([group.name, group.state.upper()])
        else:
            for group in self.groups.values():
                group_states.append([group.name, group.state.upper()])

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
        group.enable()

    def grp_disable(self, group_name):
        """Interface to disable a group"""
        group = self.get_group(group_name)
        group.disable()

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


class Resource(AttributeObject):

    def __init__(self, name, group_name):
        super(Resource, self).__init__()
        self.init_attr(resource_attributes)
        self.name = name
        self.state = ResourceStates.OFFLINE
        self.set_attr('Group', group_name)
        self.last_poll = int(time.time()) - random.randint(0, 60)  # Set at random times to prevent poll clustering
        self.poll_running = False
        self.fault_count = 0
        self.parents = []
        self.children = []
        self.propagate = False

        self.cmd_process = None
        self.cmd_type = None
        self.cmd_end_time = -1
        self.cmd_exit_code = 0

    event_map = {
        ResourceStates.OFFLINE: events.ResourceOfflineEvent,
        ResourceStates.STARTING: events.ResourceStartingEvent,
        ResourceStates.ONLINE: events.ResourceOnlineEvent,
        ResourceStates.STOPPING: events.ResourceStoppingEvent,
        ResourceStates.FAULTED: events.ResourceFaultedEvent,
        ResourceStates.UNKNOWN: events.ResourceUnknownEvent
    }

    def change_state(self, new_state, force=False):
        """Change state of resource and add event to queue"""
        cur_state = self.state
        if not force:
            if new_state is cur_state:
                return False

        if self.attr_value('Enabled') == 'false' or self.attr_value('MonitorOnly') == 'true':
            self.state = ResourceStates.OFFLINE  # Set resource offline regardless of current state
            logger.info('Resource({}) Unable to change state, resource is disabled'.format(self.name))

            # When a resource is disabled, no state change will occur. However, subsequent event will be triggered to
            # act as a pass though in order to facilitate propagation.
            # Note: A new_state of online or offline can occur when a child or parent forces a state change to continue
            # propagation when resources is already in that state.
            if new_state in [ResourceStates.STARTING, ResourceStates.ONLINE]:
                event_class = events.ResourceOnlineEvent
                cur_state = ResourceStates.ONLINE  # Fake the current state for propagation
            elif new_state in [ResourceStates.STOPPING, ResourceStates.OFFLINE]:
                event_class = events.ResourceOfflineEvent
                cur_state = ResourceStates.OFFLINE  # Fake the current state for propagation
            else:
                logger.error('Resource({}) Attempted an invalid state change to {} when resource is disabled,'
                             ' no change will occur'.format(self.name, new_state))
                return False
        else:
            self.state = new_state
            event_class = self.event_map[new_state]
            logger.info('Resource({}) Changing state from {} to {}'.format(self.name, cur_state, new_state))

        events.trigger_event(event_class(self, cur_state))

    def add_parent(self, resource):
        self.parents.append(resource)

    def remove_parent(self, resource):
        self.parents.remove(resource)

    def dependencies(self):
        """Return a list of dependencies"""
        deps_list = []
        for parent in self.parents:
            deps_list.append(parent.name)
        return deps_list

    def add_child(self, resource):
        self.children.append(resource)

    def remove_child(self, resource):
        self.children.remove(resource)

    def parents_ready(self):
        """Determine weather resources parents are ready by checking for specific conditions"""
        for parent in self.parents:
            if parent.state is ResourceStates.ONLINE:
                return True
            elif parent.attr_value('Enabled') == 'false':
                return True
            elif parent.attr_value('MonitorOnly') == 'true':
                return True

        return False

    def children_ready(self):
        """Determine weather resources children are ready by checking for specific conditions"""
        for child in self.children:
            if child.state is ResourceStates.OFFLINE:
                return True
            elif child.attr_value('Enabled') == 'false':
                return True
            elif child.attr_value('MonitorOnly') == 'true':
                return True

        return False

    def update_poll(self):
        cur_time = int(time.time())
        if self.state in ONLINE_STATES:
            poll_interval = int(self.attr_value('MonitorInterval'))
        else:
            poll_interval = int(self.attr_value('OfflineMonitorInterval'))

        if cur_time - self.last_poll >= poll_interval and not self.poll_running:
            self.poll_running = True
            logger.debug('Resource({}) ready for interval monitoring poll'.format(self.name))
            events.trigger_event(events.PollRunEvent(self))

    def _reset_cmd(self):
        self.cmd_process = None
        self.cmd_type = None
        self.cmd_end_time = -1

    def _run_cmd(self, cmd, cmd_type, timeout=None):
        """Run an resource command"""
        try:
            logger.debug('Resource({}) running command: {}'.format(self.name, ' '.join(cmd)))
            self.cmd_process = subprocess.Popen(cmd,
                                                stdout=open(ICS_RES_LOG, 'a'),
                                                stderr=open(ICS_RES_LOG, 'a'),
                                                close_fds=True)
            self.cmd_end_time = int(time.time()) + timeout
            self.cmd_type = cmd_type
        except IndexError:
            logger.error('Resource({}) unable to run command, no command given'.format(self.name))
            self._reset_cmd()
        except Exception as e:
            logger.exception('Resource({}) command caught exception {}'.format(self.name, e))
            self._reset_cmd()

    def check_cmd(self):
        """Check if resource command has finished"""
        if self.cmd_process is not None:
            if self.cmd_process.poll() is not None:
                logger.debug('Resource({}) {} command returned'.format(self.name, self.cmd_type))
                self.cmd_exit_code = self.cmd_process.poll()
                return True
            elif int(time.time()) >= self.cmd_end_time:
                logger.warning('Resource({}) timeout occurred while attempting to {}'.format(self.name, self.cmd_type))
                alerts.warning(self, 'Resource {} timeout'.format(self.cmd_type))
                self.cmd_process.kill()
                # TODO: add some action here
            else:
                return False
        else:
            return False

    poll_event_map = {
        110: events.PollOnlineEvent,
        100: events.PollOfflineEvent,
        -1: events.PollUnknownEvent
    }

    def handle_cmd(self):
        """Handle resource command return"""
        if self.cmd_type in ['start', 'stop']:
            if self.cmd_exit_code != 0:
                logger.warning('Resource({}) error occurred when running {} '
                               'command, return code {}'.format(self.name, self.cmd_type, self.cmd_exit_code))
            else:
                logger.debug('Resource({}) command {} ran successfully'.format(self.name, self.cmd_type))
            events.trigger_event(events.PollRunEvent(self))
        elif self.cmd_type == 'poll':
            if self.cmd_exit_code == 110:
                logger.debug('Resource({}) poll command found resource to be online'.format(self.name))
                event_class = self.poll_event_map[self.cmd_exit_code]
            elif self.cmd_exit_code == 100:
                logger.debug('Resource({}) poll command found resource to be offline'.format(self.name))
                event_class = self.poll_event_map[self.cmd_exit_code]
            else:
                logger.warning('Resource({}) error occurred when polling '
                               'resource, return code {}'.format(self.name, self.cmd_exit_code))
                event_class = self.poll_event_map[-1]

            self.last_poll = int(time.time())
            self.poll_running = False
            events.trigger_event(event_class(self))
        else:
            logger.error('Resource({}) received unknown command type: {}'.format(self.name, self.cmd_type))

        self._reset_cmd()

    def clear(self):
        self.fault_count = 0  # reset fault count
        if self.state is ResourceStates.FAULTED:
            self.change_state(ResourceStates.OFFLINE)

    def flush(self):
        self.propagate = False
        if self.cmd_process is not None:
            self.cmd_process.kill()
        self._reset_cmd()
        if self.state is ResourceStates.STARTING:
            self.change_state(ResourceStates.OFFLINE)
        elif self.state is ResourceStates.STOPPING:
            self.change_state(ResourceStates.ONLINE)

    def probe(self):
        """Manually trigger resource poll"""
        events.trigger_event(events.PollRunEvent(self))

    def start(self):
        """Run command to start resource"""
        logger.info('Resource({}) running command to start resource'.format(self.name))
        cmd = self.attr_value('StartProgram').split()
        if not cmd:
            logger.error('Resource({}) unable to start, attribute StartProgram not set'.format(self.name))
            self.flush()
            return
        online_timeout = int(self.attr_value('OnlineTimeout'))
        self._run_cmd(cmd, 'start', timeout=online_timeout)

    def stop(self):
        """Run command to stop resource"""
        logger.info('Resource({}) running command to stop resource'.format(self.name))
        cmd = self.attr_value('StopProgram').split()
        if not cmd:
            logger.error('Resource({}) unable to start, attribute StopProgram not set'.format(self.name))
            self.flush()
            return
        offline_timeout = int(self.attr_value('OfflineTimeout'))
        self._run_cmd(cmd, 'stop', timeout=offline_timeout)

    def poll(self):
        """Run command to poll resource"""
        logger.debug('Resource({}) running command to poll resource'.format(self.name))
        cmd = self.attr_value('MonitorProgram').split()
        if not cmd:
            logger.error('Resource({}) unable to monitor, attribute MonitorProgram not set'.format(self.name))
            self.flush()
            return
        monitor_timeout = int(self.attr_value('MonitorTimeout'))
        self._run_cmd(cmd, 'poll', timeout=monitor_timeout)


class Group(AttributeObject):

    def __init__(self, name):
        super(Group, self).__init__()
        self.init_attr(group_attributes)
        self.name = name
        self.members = []  # TODO: rename member for group class?

    @property
    def state(self):
        """Get state of group by checking state of member resources"""
        if not self.members:
            return GroupStates.UNKNOWN  # A group with no resources has an unknown state

        resource_states = []
        # Get all unique resource states
        for member in self.members:
            # Only consider enabled and not MonitorOnly resources when calculating group state
            if member.attr_value('Enabled') == 'true' and member.attr_value('MonitorOnly') == 'false':
                resource_states.append(member.state)
        states = list(set(resource_states))

        if len(states) > 1:
            return GroupStates.PARTIAL  # TODO: having multiple states does not necessarily mean a partial state
        else:
            if states[0] == ResourceStates.ONLINE:
                return GroupStates.ONLINE
            elif states[0] == ResourceStates.OFFLINE:
                return GroupStates.OFFLINE
            elif states[0] == ResourceStates.FAULTED:
                return GroupStates.FAULTED
            elif states[0] == ResourceStates.UNKNOWN:
                return GroupStates.UNKNOWN
            else:
                return GroupStates.UNKNOWN

    def add_resource(self, resource):
        self.members.append(resource)

    def delete_resource(self, resource):
        self.members.remove(resource)

    def enable(self):
        for member in self.members:
            member.set_attr('Enabled', 'true')

    def disable(self):
        for member in self.members:
            member.set_attr('Enabled', 'false')

    def start(self):
        self.flush()  # Start from clean slate
        for resource in self.members:
            if not resource.parents:
                resource.propagate = True
                if resource.state is not ResourceStates.ONLINE:
                    resource.change_state(ResourceStates.STARTING)
                else:
                    # Force resource to run online event to initiate propagation
                    # event even thought resource is already online
                    resource.change_state(ResourceStates.ONLINE, force=True)

    def stop(self):
        self.flush()  # Start from clean slate
        for resource in self.members:
            if not resource.children:
                resource.propagate = True
                if resource.state is not ResourceStates.OFFLINE:
                    resource.change_state(ResourceStates.STOPPING)
                else:
                    # Force resource to run offline event to initiate propagation
                    # event even though resource is already offline
                    resource.change_state(ResourceStates.OFFLINE, force=True)

    def flush(self):
        for resource in self.members:
            resource.flush()

    def clear(self):
        for resource in self.members:
            resource.clear()
