import logging
import operator
import os
import sys
import threading
import time
from datetime import datetime
from random import choice
from shutil import copyfile

import Pyro4 as Pyro

from ics.alerts import AlertHandler
from ics.attributes import AttributeObject, system_attributes
from ics.environment import ICS_CONF
from ics.environment import ICS_CONF_FILE
from ics.environment import ICS_ENGINE_PORT
from ics.errors import ICSError
from ics.events import event_handler
from ics.resource import Resource, Group
from ics.states import ResourceStates, TRANSITION_STATES, ONLINE_STATES
from ics.utils import read_config, write_config, hostname

logger = logging.getLogger(__name__)


class NodeSystem(AttributeObject):
    """

    Attributes:
        node_name (str): Node name.
        cluster_name (str): Cluster name.
        resources (dict): Dictionary or resource objects.
        groups (dict): Dictionary of group objects.
        threads (list): List of started thread references.
        alert_handler (obj): Alert handler object.
        remote_nodes (dict): Dictionary or remote node Pyro connections.
        poll_enabled (bool): Flag signifying when polling is enabled.
        config_update (bool): Flag signifying when there is an update to save in the config.

    """

    def __init__(self):
        super(NodeSystem, self).__init__()
        self.init_attr(system_attributes)
        self.node_name = hostname()
        self.cluster_name = ""
        self.resources = {}
        self.groups = {}
        self.threads = []
        self.alert_handler = AlertHandler(cluster_name=self.cluster_name, node_name=self.node_name)
        self.remote_nodes = {}  # Remote systems
        self.poll_enabled = False
        self.config_update = False

    @Pyro.expose
    def ping(self, host=None):
        """Dummy function for pinging node.

        Args:
            host (str): Calling node.

        Returns:
            bool: Always true.

        """
        if host is None:
            logging.debug('Received ping')
        else:
            logging.debug('Received ping from ' + str(host))
        return True

    def attr_value(self, attr):
        """Retrieve value of attribute for node.

        Args:
            attr (str): Attribute name.

        Returns:
            obj: Attribute value.

        """
        if attr == 'NodeName':
            return self.node_name
        else:
            return super().attr_value(attr)

    def attr_list(self):
        """Return a list of node attribute values and their values.

        Returns:
            list: List of attribute name, value tuples

        """
        node_attr_list = super().attr_list()
        node_attr_list.append(('NodeName', self.node_name))
        return node_attr_list

    def register_node(self, host):
        """Register a host and generate its URI.

        Args:
            host (str): Hostname of node to add.

        """
        logger.info('Registering node ' + str(host))

        if host == self.node_name:
            logger.error("Unable to register self ({}) as a remote node".format(self.node_name))
            return

        uri = 'PYRO:system@' + str(host) + ':' + str(ICS_ENGINE_PORT)
        self.remote_nodes[host] = Pyro.Proxy(uri)

    @Pyro.expose
    def add_node(self, host):
        """Add a node to the cluster.

        Args:
            host (str): Hostname of node to add.

        """
        logger.info('Adding node {}'.format(host))
        if host == self.node_name:
            logger.info('Node is same as local system, skipping...')
        else:
            self.register_node(host)
            self.attr_append_value('NodeList', host)

    @Pyro.expose
    def delete_node(self, host):
        """Delete a node from the cluster.

        Args:
            host (str): Hostname of node to add.

        """
        logger.info('Deleting node {}'.format(host))
        # TODO: Check if host is current host
        del self.remote_nodes[host]
        self.attr_remove_value('NodeList', host)

    @Pyro.expose
    def node_list(self):
        """Cluster interface for getting node list.

        Returns:
            list: Nodes withing cluster.

        """
        return self.attr_value('NodeList')

    def heartbeat(self):
        while True:
            for host in self.remote_nodes:
                try:
                    self.remote_nodes[host].ping(host=self.node_name)
                except Pyro.errors.CommunicationError as error:
                    # TODO: send alert
                    logger.debug('Heartbeat error: ' + str(error))
                    logger.error('Heartbeat from {} lost'.format(host))

            time.sleep(1)

    @Pyro.expose
    def clus_res_online(self, resource_name, system_name):
        """Online a resource in the cluster.

        Args:
            resource_name (str): Resource name.
            system_name (str): System name.

        """
        if self.attr_value('NodeName') == system_name:
            # TODO: check if online on other node first
            self.res_online(resource_name)
        else:
            self.remote_nodes[system_name].clus_res_online(resource_name, system_name)

    @Pyro.expose
    def clus_res_offline(self, resource_name, system_name):
        """Offline a resource in the cluster.
        
        Args:
            resource_name (str): Resource name.
            system_name (str): System name.

        """
        if system_name == self.node_name:
            self.res_offline(resource_name)
        else:
            self.remote_nodes[system_name].clus_res_offline(resource_name, system_name)

    @Pyro.expose
    def clus_res_add(self, resource_name, group_name, remote=False):
        """Cluster interface for adding a resource.
        
        Args:
            resource_name (str): Resource name.
            group_name (str): Resource group name. 
            remote (bool, opt): Local or remote execution. 

        """
        self.res_add(resource_name, group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_res_add(resource_name, group_name, remote=True)

    @Pyro.expose
    def clus_res_delete(self, resource_name, remote=False):
        """Cluster interface for deleting resources.
        
        Args:
            resource_name (str): Resource name. 
            remote (bool, opt): Local or remote execution.

        """
        self.res_delete(resource_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_res_delete(resource_name, remote=True)

    @Pyro.expose
    def clus_res_state(self, resource_name):
        """Return dictionary of resource states on all cluster nodes.

        Args:
            resource_name (str): Resource_name

        Returns:
            dict: Nodes with resource state

        """
        states = {
            self.attr_value('NodeName'): self.res_state(resource_name)
        }
        for node in self.remote_nodes:
            states[node] = self.remote_nodes[node].res_state(resource_name)

        return states

    @Pyro.expose
    def clus_res_state_many(self, resource_list, include_node=False, remote=False):
        """Cluster interface for setting multiple resource states.
        
        Args:
            resource_list (list): List of resource names. 
            include_node (bool, opt): Include node in states. 
            remote (bool, opt): Local or remote execution. 

        Returns:
            list: Resource states.
            
        """
        resource_states = []
        resource_states += self.res_state_many(resource_list, include_node=include_node)
        if not remote:
            for node in self.remote_nodes:
                resource_states += self.remote_nodes[node].clus_res_state_many(resource_list,
                                                                               include_node=include_node,
                                                                               remote=True)
        return resource_states

    @Pyro.expose
    def clus_res_link(self, resource_name, resource_dependency, remote=False):
        """Add a resource dependency on the cluster.
        
        Args:
            resource_name (str): Resource name. 
            resource_dependency (str) Resource dependency name.
            remote (bool, opt): Local or remote execution.

        """
        self.res_link(resource_name, resource_dependency)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_res_link(resource_name, resource_dependency, remote=True)

    @Pyro.expose
    def clus_res_unlink(self, resource_name, resource_dependency, remote=False):
        """Remove a resource dependency on the cluster.
        
        Args:
            resource_name (str): Resource name. 
            resource_dependency (str): Resource dependency name. 
            remote (bool, opt): Local or remote execution. 

        """
        self.res_unlink(resource_name, resource_dependency)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_res_unlink(resource_name, resource_dependency, remote=True)

    @Pyro.expose
    def clus_res_clear(self, resource_name, remote=False):
        """CLuster interface for clearing resource fault.
        
        Args:
            resource_name (str): Resource name. 
            remote (bool, opt): Local or remote execution.

        """
        self.res_clear(resource_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_res_clear(resource_name, remote=True)

    @Pyro.expose
    def clus_res_probe(self, resource_name):
        """Cluster interface for probing resource.
        
        Args:
            resource_name (str): Resource name.

        """
        self.res_probe(resource_name)

    @Pyro.expose
    def clus_res_dep(self, resource_args):
        """Resource dependencies.

        Args:
            resource_args (list): List of resource names to retrieve dependencies.

        Returns:
            list: List of lists with group name, resource name and dependency name.

        """
        return self.res_dep(resource_args)

    @Pyro.expose
    def clus_res_list(self):
        """Resource list.
        
        Returns:
            list: Cluster resource names.

        """
        return self.res_list()

    @Pyro.expose
    def clus_res_value(self, resource_name, attr_name):
        """Retrieve attribute value.
        
        Args:
            resource_name (str): Resource name. 
            attr_name (str): Attribute name. 

        Returns:
            str: Resource attribute value.

        """
        return self.res_value(resource_name, attr_name)

    @Pyro.expose
    def clus_res_modify(self, resource_name, attr_name, value, remote=False):
        """Modify a resource attribute on the cluster.
        
        Args:
            resource_name (str): Resource name. 
            attr_name (str): Attribute name. 
            value (str): New attribute value. 
            remote (bool, opt): Local or remote execution.

        """
        self.res_modify(resource_name, attr_name, value)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_res_modify(resource_name, attr_name, value, remote=True)

    @Pyro.expose
    def clus_res_attr(self, resource_name):
        """Retrieve resource attributes.
        
        Args:
            resource_name (str): Resource attribute name. 

        Returns:
            list: Resource attribute names. 

        """
        return self.res_attr(resource_name)

    @Pyro.expose
    def clus_grp_online(self, group_name, node=None):
        """Online group for a given system node.

        Args:
            group_name (str): Group name to online.
            node (str, opt): Node name of where to online the group.

        """
        if node is None:
            current_load = self.grp_clus_load(group_name)
            logger.debug('Valid group node loads: ' + str(current_load))
            if len(current_load.values()) == 0:
                logger.info('No valid system systems set for group {}'.format(group_name))
                raise ICSError('No valid system systems set for group {}'.format(group_name))
            elif len(set(current_load.values())) == 1:
                logger.debug("Found even load on all nodes")
                online_node = choice(list(current_load.keys()))
                logger.debug('Randomly choosing node ' + str(online_node))
            else:
                online_node = min(current_load.items(), key=operator.itemgetter(1))[0]
                logger.debug('Found minimum load node: ' + str(online_node))
        else:
            if node not in self.grp_value(group_name, 'SystemList'):
                logger.info('Invalid node for {}, node {} not in system list'.format(group_name, node))
                raise ICSError('Invalid node for {}, node {} not in system list'.format(group_name, node))
            else:
                online_node = node

        logger.debug('Attempting online group {} on node {} '.format(group_name, online_node))

        if self.attr_value('NodeName') == online_node:
            group = self.get_group(group_name)
            if group.attr_value('Parallel') == 'false':
                logger.debug('Looking for other online resources for group ' + str(group_name))
                group_remote_states = self.clus_grp_state_all(group_names=[group_name], include_local=False)
                logger.debug('Found these states on remote nodes: ' + str(group_remote_states))
                for group_name_state, remote_node, remote_state in group_remote_states:
                    if remote_state in ['ONLINE', 'PARTIAL', 'UNKNOWN']:
                        logger.info('Unable to bring group online, group is online on node ' + str(remote_node))
                        break
                else:
                    logger.debug('No other online groups found')
                    self.grp_online(group_name)
            else:
                self.grp_online(group_name)
        else:
            self.remote_nodes[online_node].clus_grp_online(group_name, online_node)

    @Pyro.expose
    def clus_grp_offline(self, group_name, node=None):
        """Offline group for a given system node.
        
        Args:
            group_name (str): Group name. 
            node (str, opt): System name.

        """
        if node is None:
            self.grp_offline(group_name)
            for remote_node in self.remote_nodes:
                self.remote_nodes[remote_node].grp_offline(group_name)
        elif self.attr_value('NodeName') == node:
            self.grp_offline(group_name)
        else:
            self.remote_nodes[node].grp_offline(group_name)

    @Pyro.expose
    def clus_grp_state(self, group_name):
        """Get a state of a group for the current node.

        Args:
            group_name (str): Group name to get state.

        Returns:
            str: Group state.

        """
        states = {
            self.attr_value('NodeName'): self.grp_state(group_name)
        }

        for node in self.remote_nodes:
            states[node] = self.remote_nodes[node].grp_state(group_name)

        return states

    @Pyro.expose
    def clus_grp_state_all(self, group_names=None, include_local=True):
        """Get all group states from all nodes in the cluster.

        Args:
            group_names (list): Limit the group name list for a given list of groups.
            include_local (bool): Toggle whether local node is included in group states.

        Returns:
            list: List of tuples with the format of (group name, node name, group state).
        """
        group_states = []
        if group_names is None:
            group_names = self.groups.keys()

        local_node = self.attr_value('NodeName')

        for group_name in group_names:

            if include_local:
                group_states.append((group_name, local_node, self.grp_state(group_name)))

            for node in self.remote_nodes:
                state = self.remote_nodes[node].grp_state(group_name)
                logger.debug("Found group {} in state {} on node {}".format(group_name, state, node))
                group_states.append((group_name, node, state))

        return group_states

    @Pyro.expose
    def clus_grp_add(self, group_name, remote=False):
        """Add a new group.

        Args:
            group_name (str): Name of group.
            remote (bool, opt): Local or remote execution.

        """
        self.grp_add(group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_add(group_name, remote=True)

    @Pyro.expose
    def clus_grp_delete(self, group_name, remote=False):
        """Remove a group from the cluster.
        
        Args:
            group_name (str): Group name. 
            remote (bool, opt): Local or remote execution. 

        """
        self.grp_delete(group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_delete(group_name, remote=True)

    @Pyro.expose
    def clus_grp_enable(self, group_name, remote=False):
        """Enable a group on the cluster.
        
        Args:
            group_name (str): Group name. 
            remote (bool, opt): Local or remote execution.

        """
        self.grp_enable(group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_enable(group_name, remote=True)

    @Pyro.expose
    def clus_grp_disable(self, group_name, remote=False):
        """Disable a group on the cluster.

        Args:
            group_name (str): Group name.
            remote (str):Local or remote execution.

        """
        self.grp_disable(group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_disable(group_name, remote=True)

    @Pyro.expose
    def clus_grp_enable_resources(self, group_name, remote=False):
        """Enable a group resources on a cluster.

        Args:
            group_name (str): Group name.
            remote (bool, opt): Local or remote execution.

        """
        self.grp_enable_resources(group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_enable_resources(group_name, remote=True)

    @Pyro.expose
    def clus_grp_disable_resources(self, group_name, remote=False):
        """Disable a group resources on a cluster.

        Args:
            group_name (str): Group name.
            remote (bool, opt): Local or remote execution.

        """
        self.grp_disable_resources(group_name)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_disable_resources(group_name, remote=True)

    @Pyro.expose
    def clus_grp_flush(self, group_name, system_name):
        """Flush a group on the cluster.

        Args:
            group_name (str): Group name.
            system_name (str): System name.

        """
        if system_name == self.node_name:
            self.grp_flush(group_name)
        else:
            self.remote_nodes[system_name].clus_grp_flush(group_name, system_name)

    @Pyro.expose
    def clus_grp_clear(self, group_name, system_name):
        """Clear a group on the cluster.

        Args:
            group_name (str): Group name.
            system_name (str): System name.

        """
        if system_name == self.node_name:
            self.grp_clear(group_name)
        else:
            self.remote_nodes[system_name].clus_grp_clear(group_name, system_name)

    @Pyro.expose
    def clus_grp_resources(self, group_name):
        """List a group resources on the cluster.

        Args:
            group_name(str): Group name.

        Returns:
            list: Group resource names.

        """
        return self.grp_resources(group_name)

    @Pyro.expose
    def clus_grp_list(self):
        """List groups on the cluster.

        Returns:
            list: Cluster group list.

        """
        return self.grp_list()

    @Pyro.expose
    def clus_grp_value(self, group_name, attr_name):
        """Get a value from a group on the cluster.

        Args:
            group_name (str): Group name.
            attr_name (str): Group attribute value.

        Returns:
            str: Group attribute value.

        """
        return self.grp_value(group_name, attr_name)

    @Pyro.expose
    def clus_grp_modify(self, group_name, attr_name, value, remote=False, append=False, remove=False):
        """Modify a group attribute value on the cluster.

        Args:
            group_name (str): Group name.
            attr_name (str): Group attribute name.
            value (str): New group attribute value.
            remote (bool, opt): Local or remote execution.
            append (bool, opt): Append item to attribute list.
            remove (bool, opt): Remove item from attribute list.

        """
        self.grp_modify(group_name, attr_name, value, append=append, remove=remove)
        if not remote:
            for node in self.remote_nodes:
                self.remote_nodes[node].clus_grp_modify(group_name, attr_name, value, remote=True, append=append,
                                                        remove=remove)

    @Pyro.expose
    def clus_grp_attr(self, group_name):
        """Get group attribute values from the cluster.

        Args:
            group_name (str): Group name.

        Returns:
            str: Group attribute value.

        """
        return self.grp_attr(group_name)

    def set_attr(self, attr, value):
        """Set node attribute value.

        Args:
            attr (str): Attribute name.
            value (str): Attribute value.

        """
        super(NodeSystem, self).set_attr(attr, value)
        if attr == "ClusterName":
            self.cluster_name = value
        elif attr == "NodeName":
            self.node_name = value

    @Pyro.expose
    def node_attr(self):
        """Return a list of node attributes"""
        return self.attr_list()

    @Pyro.expose
    def node_value(self, attr_name):
        """Return node attribute.

        Args:
            attr_name (str): Attribute name.

        Returns:
            str: Node attribute value.

        """
        return self.attr_value(attr_name)

    @Pyro.expose
    def node_modify(self, attr_name, value):
        """Modify a node attribute.

        Args:
            attr_name (str): Attribute name.
            value (str): Attribute value.

        Returns:
            bool: Stressfulness of attribute change.

        """
        try:
            self.set_attr(attr_name, value)
        except KeyError:
            return False
        return True

    def get_resource(self, resource_name):
        """Get resource object from resources list.

        Args:
            resource_name (str): Name of resource.

        Returns:
            obj: Resource object.

        Raises:
            ICSError: When resource does not exist.

        """
        if resource_name in self.resources.keys():
            resource = self.resources[resource_name]
            return resource
        else:
            raise ICSError('Resource {} does not exist'.format(resource_name))

    def res_online(self, resource_name):
        """Interface for bringing resource online.

        Args:
            resource_name (str): Resource name.

        Raises:
            ICSError: When resource has attribute MonitorOnly is enabled.

        """
        resource = self.get_resource(resource_name)
        if resource.attr_value('MonitorOnly') == 'true':
            raise ICSError('Unable to online resource, MonitorOnly mode enabled')
        if resource.state is not ResourceStates.ONLINE:
            resource.change_state(ResourceStates.STARTING)

    def res_offline(self, resource_name):
        """Interface for bringing resource offline.

        Args:
            resource_name (str): Resource name.

        """
        resource = self.get_resource(resource_name)
        if resource.attr_value('MonitorOnly') == 'true':
            raise ICSError('Unable to offline resource, MonitoryOnly mode enabled')
        if resource.state is not ResourceStates.OFFLINE:
            resource.change_state(ResourceStates.STOPPING)

    def res_add(self, resource_name, group_name, init_state=ResourceStates.OFFLINE):
        """Interface for adding new resource.

        Args:
            resource_name (str): Name of new resource.
            group_name (str): Name of existing group.
            init_state (obj, opt): Initial state of resource.

        Raises:
            ICSError: When resource already exists.
            ICSError: When group doesn't exists.
            ICSError: When max resource count is reached.

        """
        logger.info('Adding new resource {}'.format(resource_name))
        if resource_name in self.resources.keys():
            raise ICSError('Resource {} already exists'.format(resource_name))
        elif group_name not in self.groups.keys():
            raise ICSError('Group {} does not exist'.format(group_name))
        elif len(self.resources) >= int(self.attr_value('ResourceLimit')):
            raise ICSError('Max resource count reached, unable to add new resource')
        else:
            resource = Resource(resource_name, group_name, init_state=init_state)
            self.resources[resource_name] = resource
            group = self.groups[group_name]
            group.add_resource(resource)

        self.config_update = True

    def res_delete(self, resource_name):
        """Interface for deleting existing resource.

        Args:
            resource_name (str): Resource name.

        Raises:
            ICSError: If resource does not exist.

        """
        resource = self.get_resource(resource_name)

        for parent in resource.parents:
            parent.children.remove(resource)

        for child in resource.children:
            child.parents.remove(resource)

        group = self.get_group(resource.attr_value('Group'))
        group.delete_resource(resource)
        del self.resources[resource_name]
        self.config_update = True
        logger.info('Resource({}) resource deleted'.format(resource_name))

    @Pyro.expose
    def res_state(self, resource_name):
        """Return state for a given resource.

        Args:
            resource_name (str): Resource name.

        Returns:
            str: String representation of resource state in all upper case.

        """
        resource = self.get_resource(resource_name)
        return resource.state.upper()

    def res_state_many(self, resource_list, include_node=False):
        """Return states for a given list of resource.

        Args:
            resource_list (list): List of resource names.
            include_node: Include node name in output.

        Returns:
            list: resource names with resource states.

        """
        resources = []
        resource_states = []
        node_name = self.attr_value('NodeName')

        if resource_list:
            for resource_name in resource_list:
                resources.append(self.get_resource(resource_name))
        else:
            resources = self.resources.values()

        for resource in resources:
            if include_node:
                resource_states.append([resource.name, node_name, resource.state.upper()])
            else:
                resource_states.append([resource.name, resource.state.upper()])

        return resource_states

    def res_link(self, resource_name, resource_dependency):
        """Interface to add a dependency to a resource.

        Args:
            resource_name (str): Resource name.
            resource_dependency (str): Resource to be added as a dependency to resource_name.

        Raises:
            ICSError: When resources given are not in the same group.

        """
        resource = self.get_resource(resource_name)
        parent_resource = self.get_resource(resource_dependency)
        if resource.attr_value('Group') != parent_resource.attr_value('Group'):
            raise ICSError('Unable to add link, resources not in same group')
        resource.add_parent(parent_resource)
        parent_resource.add_child(resource)
        logger.info('Resource({}) created dependency on {}'.format(resource_name, resource_dependency))
        self.config_update = True

    def res_unlink(self,  resource_name, resource_dependency):
        """Interface to remove a dependency from a resource.

        Args:
            resource_name (str): Resource name.
            resource_dependency (str): Resource to be removed as a dependency from resource_name.

        Raises:
            ICSError: When resource link does not exist.

        """
        resource = self.get_resource(resource_name)
        parent_resource = self.get_resource(resource_dependency)
        try:
            resource.remove_parent(parent_resource)
        except ValueError:
            raise ICSError('Unable to remove link, link does not exist.')
        parent_resource.remove_child(resource)
        logger.info('Resource({}) removed dependency on {}'.format(resource_name, resource_dependency))
        self.config_update = True

    def res_dep(self, resource_names):
        """Interface for getting resource dependencies.

        Args:
            resource_names (list): List of resource names to retrieve dependencies.

        Returns:
            list: List of lists with group name, resource name and dependency name

        """
        dep_list = []
        if len(resource_names) == 0:
            for resource in self.resources.values():
                resource_group_name = resource.attr_value('Group')
                for parent in resource.parents:
                    row = [resource_group_name, resource.name, parent.name]
                    dep_list.append(row)
        else:
            for resource_name in resource_names:
                resource = self.get_resource(resource_name)
                resource_group_name = resource.attr_value('Group')
                for parent in resource.parents:
                    row = [resource_group_name, resource.name, parent.name]
                    dep_list.append(row)
                for child in resource.children:
                    row = [resource_group_name, resource.name, child.name]
                    dep_list.append(row)

        return dep_list

    def res_clear(self, resource_name):
        """Interface for clearing resource in a faulted state.

        Args:
            resource_name (str): Resource name.

        """
        resource = self.get_resource(resource_name)
        resource.clear()

    def res_probe(self, resource_name):
        """Interface for manually triggering a poll.

        Args:
            resource_name (str): Resource name.

        """
        resource = self.get_resource(resource_name)
        resource.probe()

    def res_list(self):
        """Interface for listing all resources.

        Returns:
            list: List of all resources within node.

        """
        return list(self.resources.keys())

    def res_value(self, resource_name, attr_name):
        """Interface for getting attribute value for resource.

        Args:
            resource_name (str): Resource name.
            attr_name (str): Resource attribute name.

        Returns:
            str: Resource attribute value.

        """
        resource = self.get_resource(resource_name)
        return resource.attr_value(attr_name)

    def res_modify(self, resource_name, attr_name, value):
        """Interface for modifying attribute for resource.

        Args:
            resource_name (str): Resource name.
            attr_name (str): Resource attribute name.
            value (str): Resource attribute name.

        Returns:
            bool: True if attribute exists, false is not.

        """
        resource = self.get_resource(resource_name)
        try:
            resource.set_attr(attr_name, value)
        except KeyError:
            return False
        return True

    def res_attr(self, resource_name):
        """Interface for getting resource attributes.

        Args:
            resource_name (str): Resource name.

        Returns:
            list: List of tuples with attribute name and value.

        """
        resource = self.get_resource(resource_name)
        return resource.attr_list()

    def get_group(self, group_name):
        """Get group object from groups list.

        Args:
            group_name (str): Name of group

        Returns:
            obj: Group object.

        Raises:
            ICSError: When group does not exist.

        """
        if group_name in self.groups.keys():
            group = self.groups[group_name]
            return group
        else:
            raise ICSError('Group {} does not exist'.format(group_name))

    def grp_online(self, group_name):
        """Interface for bringing a group online.

        Args:
            group_name (str): Group name.

        """
        logger.info('Group({}) bringing online'.format(group_name))
        group = self.get_group(group_name)
        group.start()

    def grp_online_auto(self):
        """Start all groups with the attribute AutoStart set to true."""
        for group in self.groups.values():
            if group.attr_value('AutoStart') == 'true':
                group.start()

    @Pyro.expose
    def grp_offline(self, group_name):
        """Interface for bringing a group offline.

        Args:
            group_name (str): Group name.

        """
        logger.info('Group({}) bringing offline'.format(group_name))
        group = self.get_group(group_name)
        group.stop()

    @Pyro.expose
    def grp_state(self, group_name):
        """Interface for getting state of group.

        Args:
            group_name (str): Name of group.

        Returns:
            str: Group state.

        """
        group = self.get_group(group_name)
        return group.state().upper()

    def grp_add(self, group_name):
        """Interface for adding a new group.

        Args:
            group_name (str): Group name.

        Raises:
            ICSError: When group already exist.
            ICSError: When max group count has been reached.

        """
        logger.info('Adding new group {}'.format(group_name))
        if group_name in self.grp_list():
            raise ICSError('Group {} already exists'.format(group_name))
        elif len(self.groups) >= int(self.attr_value('GroupLimit')):
            raise ICSError('Max group count reached, unable to add new group')
        else:
            group = Group(group_name)
            self.groups[group_name] = group

        self.config_update = True

    def grp_delete(self, group_name):
        """Interface for deleting an existing group.

        Args:
            group_name (str): Group name.

        """
        logger.info('Deleting group {}'.format(group_name))
        group = self.get_group(group_name)
        if not group.members:
            del self.groups[group_name]
        else:
            logger.error('Unable to delete group ({}), group still contains resources'.format(group_name))
            pass  # delete object?

        self.config_update = True

    def grp_enable(self, group_name):
        """Interface to enable a group.

        Args:
            group_name (str): Group name.

        """
        group = self.get_group(group_name)
        group.set_attr('Enabled', 'true')

    def grp_disable(self, group_name):
        """Interface to disable a group.

        Args:
            group_name (str): Group name.

        """
        group = self.get_group(group_name)
        group.set_attr('Enabled', 'false')

    def grp_enable_resources(self, group_name):
        """Interface to enable a group resources.

        Args:
            group_name (str): Group name.

        """
        group = self.get_group(group_name)
        group.enable_resources()

    def grp_disable_resources(self, group_name):
        """Interface to disable a group resources.

        Args:
            group_name (str): Group name.

        """
        group = self.get_group(group_name)
        group.disable_resources()

    def grp_flush(self, group_name):
        """Interface for flushing a group.

        Args:
            group_name (str): Group name.

        """
        group = self.get_group(group_name)
        group.flush()

    def grp_clear(self, group_name):
        """Interface for clearing a group.

        Args:
            group_name (str): Group name.

        """
        group = self.get_group(group_name)
        group.clear()

    def grp_resources(self, group_name):
        """Interface for getting members of a group.

        Args:
            group_name (str): Group name.

        Returns:
            list: Resource name list of given group.

        """
        group = self.get_group(group_name)
        resource_names = []
        for member in group.members:
            resource_names.append(member.name)
        return resource_names

    def grp_list(self):
        """Interface for listing all existing group names

        Returns:
            list: System group names.
        """
        return list(self.groups.keys())

    def grp_value(self, group_name, attr_name):
        """Return an attribute for a given group and attribute.

        Args:
            group_name (str): Group name.
            attr_name (str): Attribute name.

        Returns:
            str: Group attribute value.
        """
        group = self.get_group(group_name)
        return group.attr_value(attr_name)

    def grp_modify(self, group_name, attr_name, value, append=False, remove=False):
        """Modify an attribute for a given group.

        Args:
            group_name (str): Group name.
            attr_name (str): Group attribute name.
            value (str): Group attribute value.
            append (bool, opt): Append item to attribute list.
            remove (bool, opt): Remove item from attribute list.

        Returns:
            bool: Stressfulness of attribute modification.

        """
        group = self.get_group(group_name)
        try:
            if append:
                logger.debug('Group({}) Appending {} to attribute {} '.format(group_name, value, attr_name))
                group.attr_append_value(attr_name, value)
            elif remove:
                logger.debug('Group({}) Removing {} from  attribute {}'.format(group_name, value, attr_name))
                group.attr_remove_value(attr_name, value)
            else:
                logger.debug('Group({}) Modifying attribute {} to {} '.format(group_name, attr_name, value))
                group.set_attr(attr_name, value)
        except KeyError:
            return False
        return True

    def grp_attr(self, group_name):
        """Return a list of attributes for a given group.

        Args:
            group_name (str): Group name.

        Returns:
            list: List of tuples with attribute name and value.

        """
        group = self.get_group(group_name)
        return group.attr_list()

    @Pyro.expose
    def clus_load(self):
        """Retrieve load value from all nodes in cluster.

        Returns:
            dict: Nodes with current load value.

        """

        nodes_load = {self.attr_value('NodeName'):  self.load()}

        for node in self.remote_nodes:
            nodes_load[node] = self.remote_nodes[node].load()

        logger.debug('Node loads: ' + str(nodes_load))
        return nodes_load

    def grp_clus_load(self, group_name):
        """Retrieve load value from all valid nodes in the cluster for a given group.

        Args:
            group_name (str): Group name.

        Returns:
            dict: Valid group nodes with current load value.


        """
        group_nodes_load = {}
        nodes_load = self.clus_load()

        for node in self.grp_value(group_name, 'SystemList'):
            group_nodes_load[node] = nodes_load[node]

        return group_nodes_load

    @Pyro.expose
    def load(self):
        """Calculate total current resource load on node.

        Returns:
            int: total node load.

        """
        total_load = 0
        for group in self.groups.values():
            if group.state() in ONLINE_STATES:
                total_load += group.load()

        return total_load

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
                    if self.poll_enabled:
                        resource.update_poll()
            time.sleep(1)

    def poll_count(self):
        """Return amount of resources currently being polled"""
        count = 0
        for resource in self.resources.values():
            if resource.poll_running:
                count += 1
        return count

    def startup_poll(self):
        """Poll all resources"""
        logger.info('Polling resources to determine initial state...')
        resource_count = len(self.resources)
        polled_resources = 0
        for resource in self.resources.values():
            while True:
                count = self.poll_count()
                if count < 30:
                    resource.probe()
                    polled_resources += 1
                    logger.info('Remaining resources to be polled {}/{}'.format(str(resource_count - polled_resources),
                                                                                str(resource_count)))
                    break
                else:
                    time.sleep(0.1)

        # Wait for all polls to finish
        while self.poll_count() != 0:
            time.sleep(1)

        logger.info('Startup polling complete')

    def start_event_handler(self):
        """Start event handler thread"""
        logger.info('Starting event handler...')
        thread_event_handler = threading.Thread(name='event handler', target=event_handler)
        thread_event_handler.daemon = True
        thread_event_handler.start()
        self.threads.append(thread_event_handler)

    def start_poll_updater(self):
        """Start poll updater thread"""
        logger.info('Starting poll updater...')
        thread_poll_updater = threading.Thread(name='poll updater', target=self.poll_updater)
        thread_poll_updater.daemon = True
        thread_poll_updater.start()
        self.threads.append(thread_poll_updater)

    def start_threads(self):
        """Start subsystem threads."""
        # Start alert handler thread
        logger.info('Starting alert handler...')
        thread_alert_handler = threading.Thread(name='alert handler', target=self.alert_handler.run)
        thread_alert_handler.daemon = True
        thread_alert_handler.start()
        self.threads.append(thread_alert_handler)

        # Start config backup
        logger.info('Starting auto backups...')
        thread_config_backup = threading.Thread(name='backup config', target=self.backup_config)
        thread_config_backup.daemon = True
        thread_config_backup.start()
        self.threads.append(thread_config_backup)

        # Start heartbeat thread
        # logger.info('Starting heartbeat thread...')
        # thread_heartbeat = threading.Thread(name='heartbeat', target=self.heartbeat)
        # thread_heartbeat.daemon = True
        # thread_heartbeat.start()
        # self.threads.append(thread_heartbeat)

    @Pyro.expose
    def dump(self):

        data = {
            'data': {
                'system': {},
                'groups': {},
                'resources': {},
            }
        }

        dumped_sys_attr = ['ClusterName', 'NodeName', 'NodeList']
        dumped_grp_attr = ['Enabled', 'SystemList', 'Parallel']
        dumped_res_attr = ['Enabled', 'Group', 'Load']

        for attr in dumped_sys_attr:
            data['data']['system'][attr] = self.attr_value(attr)

        for group_name, group in self.groups.items():
            data['data']['groups'][group_name] = {'State': self.clus_grp_state(group_name)}
            for attr in dumped_grp_attr:
                data['data']['groups'][group_name][attr] = group.attr_value(attr)

        for resource_name, resource in self.resources.items():
            data['data']['resources'][resource_name] = {'State': self.clus_res_state(resource_name)}
            for attr in dumped_res_attr:
                data['data']['resources'][resource_name][attr] = resource.attr_value(attr)

        return data

    @Pyro.expose
    def clus_log_command(self, message):
        """Log command onto cluster.

        Args:
            message (str): Message to log.

        """
        self.log_command(message)
        for node in self.remote_nodes:
            self.remote_nodes[node].log_command(message)

    @Pyro.expose
    def log_command(self, message):
        """Log message.

        Args:
            message (str): Message to log.

        """
        logger.info('User command, ' + str(message))

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
        """Load system config file.

        Args:
            data (dict): System configuration data.

        """
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
                self.grp_add(group_name)
                group = self.get_group(group_name)
                for attr_name in group_data[group_name]['attributes']:
                    group.set_attr(attr_name, group_data[group_name]['attributes'][attr_name])

            # Create resources from config
            resource_data = data['resources']
            for resource_name in resource_data.keys():
                group_name = resource_data[resource_name]['attributes']['Group']
                self.res_add(resource_name, group_name, init_state=ResourceStates.UNKNOWN)
                resource = self.get_resource(resource_name)
                for attr_name in resource_data[resource_name]['attributes']:
                    resource.set_attr(attr_name, resource_data[resource_name]['attributes'][attr_name])

            # Create resource dependency links
            # Note: Links need to be done in separate loop to guarantee parent resources
            # are created first when establishing links
            for resource_name in resource_data.keys():
                for dep_name in resource_data[resource_name]['dependencies']:
                    self.res_link(resource_name, dep_name)
        except (TypeError, KeyError) as error:
            logging.error('Error occurred while loading config: {}:{}'.format(error.__class__.__name__, str(error)))
            raise

    def backup_config(self):
        """Continuously write backup system config file."""
        while True:
            interval = int(self.attr_value('BackupInterval'))

            if any([AttributeObject.update_flag, self.config_update]):
                AttributeObject.update_flag = False
                self.config_update = False
                logger.debug('Creating backup of config file')
                if os.path.isfile(ICS_CONF_FILE):
                    os.rename(ICS_CONF_FILE, ICS_CONF_FILE + '.autobackup')
                write_config(ICS_CONF_FILE, self.config_data())

                backup_file = ICS_CONF_FILE + '.' + datetime.now().strftime('%y%m%d_%H%M%S')
                logger.info('Creating backup config ' + backup_file)
                copyfile(ICS_CONF_FILE, backup_file)

            time.sleep(interval * 60)

    def startup(self):
        """Startup system."""
        logger.info('Server starting up...')
        # TODO: Add config startup management here
        data = {}
        try:
            data = read_config(ICS_CONF_FILE)
        except FileNotFoundError:
            if not os.path.exists(ICS_CONF):
                os.makedirs(ICS_CONF)

        if data:
            try:
                self.load_config(data)
            except Exception as e:
                logger.critical('Error reading config data: {}'.format(str(e)))
                sys.exit(1)  # TODO: better system handling
        else:
            logger.info('No configuration data found')

        if self.node_name not in self.attr_value('NodeList'):
            self.attr_append_value('NodeList', self.node_name)

        # Register remote nodes from config
        for host in self.attr_value('NodeList'):
            if host != self.node_name:
                self.register_node(host)

        self.start_event_handler()
        self.start_poll_updater()
        self.startup_poll()
        self.poll_enabled = True
        self.start_threads()
        self.grp_online_auto()

        logger.info('Server startup complete')

    def run(self):
        """Run system."""
        pass
        # while True:
        #     for thread in self.threads:
        #         if not thread.is_alive():
        #             logger.critical('Thread {} no longer running'.format(thread.name))
        #             #TODO: send alert that thread is no longer running
        #     time.sleep(5)

    def shutdown(self):
        """Shutdown systemm."""
        logger.info('Server shutting down...')
        write_config(ICS_CONF_FILE, self.config_data())
        self.poll_enabled = False
        logger.info('Server shutdown complete')
        logger.shutdown()
