import logging
import random
import subprocess
import time

import events
from environment import ICS_RES_LOG
from alerts import AlertSeverity, send_alert
from attributes import resource_attributes, group_attributes
from custom_exceptions import DoesNotExist, AlreadyExists
from states import ResourceStates, GroupStates, ONLINE_STATES, TRANSITION_STATES

logger = logging.getLogger(__name__)

resources = {}


class Resource:

    def __init__(self, name, group_name):
        self.name = name
        self.attr = {}
        self.state = ResourceStates.OFFLINE
        self.init_attr()
        self.attr['Group'] = group_name
        self.last_poll = int(time.time()) - random.randint(0, 60)  # Prevent poll clustering
        self.poll_running = False
        self.fault_count = 0
        self.parents = []
        self.children = []
        self.propagate = False

        self.cmd_p = None
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

        if self.attr['Enabled'] == 'false':
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
                logger.error('Resource({}) Attempted an invalid state change to {} when resource is disabled,'\
                             ' no change will occur'.format(self.name, new_state))
                return False
        else:
            self.state = new_state
            event_class = self.event_map[new_state]
            logger.info('Resource({}) Changing state from {} to {}'.format(self.name, cur_state, new_state))

        events.trigger_event(event_class(self, cur_state))

    def init_attr(self):
        for attribute in resource_attributes['resource'].keys():
            self.attr[attribute] = resource_attributes['resource'][attribute]['default']

    def set_attr(self, attr, value):
        self.attr[attr] = value

    def get_attr(self, attr):
        return self.attr[attr]

    def add_parent(self, resource):
        self.parents.append(resource)

    def remove_parent(self, resource):
        self.parents.remove(resource)

    def add_child(self, resource):
        self.children.append(resource)

    def remove_child(self, resource):
        self.children.remove(resource)

    def parents_ready(self):
        for parent in self.parents:
            if parent.state is not ResourceStates.ONLINE and parent.attr['Enabled'] == 'true':
                return False
        return True

    def children_ready(self):
        for child in self.children:
            if child.state is not ResourceStates.OFFLINE and child.attr['Enabled'] == 'true':
                return False
        return True

    def update_poll(self):
        cur_time = int(time.time())
        if self.state in ONLINE_STATES:
            poll_interval = int(self.attr['MonitorInterval'])
        else:
            poll_interval = int(self.attr['OfflineMonitorInterval'])

        if cur_time - self.last_poll >= poll_interval and not self.poll_running:
            self.poll_running = True
            logger.debug('Resource({}) ready for interval monitoring poll'.format(self.name))
            events.trigger_event(events.PollRunEvent(self))

    def clear(self):
        self.fault_count = 0  # reset fault count
        if self.state is ResourceStates.FAULTED:
            self.change_state(ResourceStates.OFFLINE)

    def _reset_cmd(self):
        self.cmd_p = None
        self.cmd_type = None
        self.cmd_end_time = -1

    def flush(self):
        self.propagate = False
        if self.cmd_p is not None:
            self.cmd_p.kill()
        self._reset_cmd()
        if self.state is ResourceStates.STARTING:
            self.change_state(ResourceStates.OFFLINE)
        elif self.state is ResourceStates.STOPPING:
            self.change_state(ResourceStates.ONLINE)

    def _run_cmd(self, cmd, cmd_type, timeout=None):
        """Run an resource command"""
        try:
            logger.debug('Resource({}) running command: {}'.format(self.name, ' '.join(cmd)))
            self.cmd_p = subprocess.Popen(cmd,
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
        if self.cmd_p is not None:
            if self.cmd_p.poll() is not None:
                logger.debug('Resource({}) {} command returned'.format(self.name, self.cmd_type))
                self.cmd_exit_code = self.cmd_p.poll()
                return True

            elif int(time.time()) >= self.cmd_end_time:
                logger.warning('Resource({}) timeout occurred while attempting to {}'.format(self.name, self.cmd_type))
                send_alert(self, AlertSeverity.WARNING, reason='Resource {} timeout'.format(self.cmd_type))
                self.cmd_p.kill()
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
                logger.warning('Resource({}) error occurred when running {} command, return code {}'
                                .format(self.name, self.cmd_type, self.cmd_exit_code))
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
                logger.warning('Resource({}) error occurred when polling resource, return code {}'
                                .format(self.name, self.cmd_exit_code))
                event_class = self.poll_event_map[-1]

            self.last_poll = int(time.time())
            self.poll_running = False
            events.trigger_event(event_class(self))
        else:
            logger.error('Resource({}) received unknown command type'.format(self.name))

        self._reset_cmd()

    def start(self):
        """Run command to start resource"""
        logger.info('Resource({}) running command to start resource'.format(self.name))
        cmd = self.attr['StartProgram'].split()
        if not cmd:
            logger.error('Resource({}) unable to start, attribute StartProgram not set'.format(self.name))
            self.flush()
            return
        online_timeout = int(self.attr['OnlineTimeout'])
        self._run_cmd(cmd, 'start', timeout=online_timeout)

    def stop(self):
        """Run command to stop resource"""
        logger.info('Resource({}) running command to stop resource'.format(self.name))
        cmd = self.attr['StopProgram'].split()
        if not cmd:
            logger.error('Resource({}) unable to start, attribute StopProgram not set'.format(self.name))
            self.flush()
            return
        offline_timeout = int(self.attr['OfflineTimeout'])
        self._run_cmd(cmd, 'stop', timeout=offline_timeout)

    def poll(self):
        """Run command to poll resource"""
        logger.debug('Resource({}) running command to poll resource'.format(self.name))
        cmd = self.attr['MonitorProgram'].split()
        if not cmd:
            logger.error('Resource({}) unable to monitor, attribute MonitorProgram not set'.format(self.name))
            self.flush()
            return
        monitor_timeout = int(self.attr['MonitorTimeout'])
        self._run_cmd(cmd, 'poll', timeout=monitor_timeout)


def poll_updater():
    """Continuously check for resources ready for poll"""
    while True:
        for resource in resources.values():
            if resource.attr['Enabled'] == 'false':
                logger.debug('Resource({}) is not enabled, skipping poll'.format(resource.name))
                continue
            elif resource.cmd_p is not None:
                if resource.check_cmd():
                    resource.handle_cmd()
            elif resource.state in TRANSITION_STATES:
                continue
            else:
                resource.update_poll()
        time.sleep(1)


groups = {}


class Group:
    def __init__(self, name):
        self.name = name
        self.members = []  # TODO: rename member for group class?
        self.attr = {}
        self.load_attr()

    @property
    def state(self):
        """Get state of group by checking state of member resources"""
        if not self.members:
            return GroupStates.UNKNOWN  # A group with no resources has an unknown state

        resource_states = []
        # Get all unique resource states
        for member in self.members:
            if member.attr['Enabled'] == 'true':  # Only consider enabled resources when calculating group state
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

    def load_attr(self):
        for attribute in group_attributes.keys():
            self.attr[attribute] = group_attributes[attribute]['default']

    def add_resource(self, resource):
        self.members.append(resource)

    def delete_resource(self, resource):
        self.members.remove(resource)

    def enable(self):
        for member in self.members:
            member.attr['Enabled'] = 'true'

    def disable(self):
        for member in self.members:
            member.attr['Enabled'] = 'false'

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


def get_resource(resource_name):
    """Get resource object from resources list"""
    if resource_name in resources.keys():
        resource = resources[resource_name]
        return resource
    else:
        raise DoesNotExist(msg='Resource {} does not exist'.format(resource_name))


def res_online(resource_name):
    """RPC interface for bringing resource online"""
    resource = get_resource(resource_name)
    if resource.state is not ResourceStates.ONLINE:
        resource.change_state(ResourceStates.STARTING)


def res_offline(resource_name):
    """RPC interface for bringing resource offline"""
    resource = get_resource(resource_name)
    if resource.state is not ResourceStates.OFFLINE:
        resource.change_state(ResourceStates.STOPPING)


def res_add(resource_name, group_name):
    """RPC interface for adding new resource"""
    if resource_name in resources.keys():
        raise AlreadyExists(msg='Resource {} already exists'.format(resource_name))
    elif group_name not in groups.keys():
        raise DoesNotExist(msg='Group {} does not exist'.format(group_name))
    else:
        resource = Resource(resource_name, group_name)
        resources[resource_name] = resource
        group = groups[group_name]
        group.add_resource(resource)
        logger.info('Resource({}) new resource added'.format(resource_name))


def res_delete(resource_name):
    """RPC interface for deleting existing resource"""
    resource = get_resource(resource_name)

    for parent in resource.parents:
        parent.children.remove(resource)

    for child in resource.children:
        child.parents.remove(resource)

    group = get_group(resource.attr['Group'])
    group.delete_resource(resource)
    del resources[resource_name]
    logger.info('Resource({}) resource deleted'.format(resource_name))


def res_state(resource_args):
    """RPC interface for getting resource current state """
    resource_states = []
    if len(resource_args) == 1:
        resource = get_resource(resource_args[0])
        resource_states.append([resource.state.upper()])
    elif resource_args:
        for resource_name in resource_args:
            resource = get_resource(resource_name)
            resource_states.append([resource.name, resource.state.upper()])
    else:
        for resource in resources.values():
            resource_states.append([resource.name, resource.state.upper()])

    return resource_states


def res_link(parent_name, resource_name):
    """RPC interface to link two resources"""
    resource = get_resource(resource_name)
    parent_resource = get_resource(parent_name)
    if resource.attr['Group'] != parent_resource.attr['Group']:
        raise Exception

    resource.add_parent(parent_resource)
    parent_resource.add_child(resource)
    logger.info('Resource({}) created dependency on {}'.format(resource_name, parent_name))


def res_unlink(parent_name, resource_name):
    """RPC interface to unlink two resources"""
    resource = get_resource(resource_name)
    parent_resource = get_resource(parent_name)
    resource.remove_parent(parent_name)
    parent_resource.remove_child(resource)


def res_clear(resource_name):
    """RPC interface for clearing resource in a faulted state"""
    resource = get_resource(resource_name)
    resource.clear()


def res_probe(resource_name):
    """RPC interface for manually triggering a poll"""
    resource = get_resource(resource_name)
    events.trigger_event(events.PollRunEvent(resource))


def res_dep(resource_args):
    """RPC interface for getting resource dependencies"""
    dep_list = []
    if len(resource_args) == 0:
        for resource in resources.values():
            resource_group_name = resource.attr['Group']
            for parent in resource.parents:
                row = [resource_group_name, parent.name, resource.name]
                dep_list.append(row)
    else:
        for resource_name in resource_args:
            resource = get_resource(resource_name)
            resource_group_name = resource.attr['Group']
            for parent in resource.parents:
                row = [resource_group_name, parent.name, resource.name]
                dep_list.append(row)
            for child in resource.children:
                row = [resource_group_name, resource.name, child.name]
                dep_list.append(row)

    return dep_list


def res_list():
    """RPC interface for listing all resources"""
    return resources


def res_value(resource_name, attr_name):
    """RPC interface for getting attribute value for resource"""
    resource = get_resource(resource_name)
    return resource.attr[attr_name]


def res_modify(resource_name, attr_name, value):
    """RPC interface for modifying attribute for resource"""
    resource = resources[resource_name]
    try:
        resource.attr[attr_name] = value
        return True
    except KeyError:
        return False


def res_attr(resource_name):
    """RPC interface for getting resource attributes"""
    resource = get_resource(resource_name)
    attr_dict = []
    for attr_name in resource.attr.keys():
        attr_dict.append([attr_name, resource.attr[attr_name]])
    return attr_dict


def get_group(group_name):
    """Get group object from groups list"""
    if group_name in groups.keys():
        group = groups[group_name]
        return group
    else:
        raise DoesNotExist(msg='Group {} does not exist'.format(group_name))


def grp_online(group_name):
    """RPC interface for bringing a group online"""
    logger.info('Group({}) bringing online'.format(group_name))
    group = get_group(group_name)
    group.start()


def grp_offline(group_name):
    """RPC interface for bringing a group offline"""
    logger.info('Group({}) bringing offline'.format(group_name))
    group = get_group(group_name)
    group.stop()


def grp_state(group_args):
    """RPC interface for getting state of group"""
    group_states = []
    if len(group_args) == 1:
        group = get_group(group_args[0])
        group_states.append([group.state.upper()])
    elif group_args:
        for group_name in group_args:
            group = get_group(group_name)
            group_states.append([group.name, group.state.upper()])
    else:
        for group in groups.values():
            group_states.append([group.name, group.state.upper()])

    return group_states


def grp_add(group_name):
    """RPC interface for adding a new group"""
    logger.info('Adding new group {}'.format(group_name))
    if group_name in groups.keys():
        raise AlreadyExists(msg='Group {} already exists'.format(group_name))
    else:
        group = Group(group_name)
        groups[group_name] = group


def grp_delete(group_name):
    """RPC interface for deleting an existing group"""
    logger.info('Deleting group {}'.format(group_name))
    group = get_group(group_name)
    if not group.members:
        del groups[group_name]
    else:
        logger.error('Unable to delete group ({}), group still contains resources'.format(group_name))

        pass  # delete object?


def grp_enable(group_name):
    """RPC interface to enable a group"""
    group = get_group(group_name)
    group.enable()


def grp_disable(group_name):
    """RPC interface to disable a group"""
    group = get_group(group_name)
    group.disable()


def grp_flush(group_name):
    """RPC interface for flushing a group"""
    group = get_group(group_name)
    group.flush()


def grp_clear(group_name):
    """RPC interface for clearing a group"""
    group = get_group(group_name)
    group.clear()


def grp_resources(group_name):
    """RPC interface for getting members of a group"""
    group = get_group(group_name)
    resource_names = []
    for member in group.members:
        resource_names.append(member.name)
    return resource_names


def grp_list():
    """RPC interface for listing all existing group names"""
    return groups.keys()
