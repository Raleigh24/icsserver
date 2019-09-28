import logging
import time

import Pyro4 as Pyro

from system import NodeSystem

logger = logging.getLogger(__name__)


class Cluster:

    def __init__(self):
        self.node_system = NodeSystem()  # Local Node system
        self.remote_systems = {}  # Remote systems
        self.node_name = ""

    def startup(self):
        self.node_system.startup()

    @Pyro.expose
    def ping(self, host=None):
        if host is None:
            logging.debug('Received ping')
        else:
            logging.debug('Received ping from ' + str(host))
        return True

    @Pyro.expose
    def add_node(self, host):
        """Add a node to the cluster"""
        logger.info('Adding node {}'.format(host))
        uri = 'PYRO:system@' + str(host) + ':9090'
        self.remote_systems[host] = Pyro.Proxy(uri)

    @Pyro.expose
    def delete_node(self, host):
        """Delete a node from the cluster"""
        logger.info('Deleting node {}'.format(host))
        del self.remote_systems[host]

    def heartbeat(self):
        while True:
            for host in self.remote_systems:
                try:
                    self.remote_systems[host].ping(host=self.node_name)
                except Pyro.errors.CommunicationError as error:
                    # TODO: send alert
                    logger.debug('Heartbeat error: ' + str(error))
                    logger.error('Heartbeat from {} lost'.format(host))

            time.sleep(1)

    # def node_connect(self, host):
    #     logging.info('Connecting to node: {}'.format(host))
    #     uri = 'PYRO:system@' + str(host) + ':9090'
    #     self.remote_node_obj[host] = Pyro.Proxy(uri)
    #     try:
    #         self.remote_node_obj[host].ping()
    #     except Pyro.errors.CommunicationError:
    #         logger.error('Unable to connect to {}'.format(host))
    #
    # def cluster_connect(self):
    #      """Estabish """
    #      pass
    #      #for node in nodes:
    #      #    self.node_connect(node)

    @Pyro.expose
    def node_attr(self):
        """Get node attributes from the cluster"""
        return self.node_system.node_attr()

    @Pyro.expose
    def node_value(self, attr_name):
        """Get a node attribute value from the cluster"""
        return self.node_system.node_value(attr_name)

    @Pyro.expose
    def node_modify(self, attr_name, value):
        """Modify a node attribute value on the cluster"""
        return self.node_system.node_modify(attr_name, value)

    @Pyro.expose
    def clus_res_online(self, resource_name, system_name):
        """Online a resource in the cluster"""
        if self.node_system.attr_value('NodeName') == system_name:
            # TODO: check if online on other node first
            self.node_system.res_online(resource_name)
        else:
            self.remote_systems[system_name].clus_res_online(resource_name, system_name)

    @Pyro.expose
    def clus_res_offline(self, resource_name, system_name):
        """Offline a resource in the cluster"""
        if system_name == self.node_name:
            self.node_system.res_offline(resource_name)
        else:
            self.remote_systems[system_name].clus_res_offline(resource_name, system_name)

    @Pyro.expose
    def clus_res_add(self, resource_name, group_name, remote=False):
        """Add a resource to the cluster"""
        self.node_system.res_add(resource_name, group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_res_add(resource_name, group_name, remote=True)

    @Pyro.expose
    def clus_res_delete(self, resource_name, remote=False):
        """Delete a resource from the cluster"""
        self.node_system.res_delete(resource_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_res_delete(resource_name, remote=True)

    @Pyro.expose
    def clus_res_state(self, resource_args):
        """Get states of a resource on the cluster"""
        # TODO: get states from other nodes
        return self.node_system.res_state(resource_args)

    @Pyro.expose
    def clus_res_state_many(self, resource_list, include_node=False, remote=False):
        resource_states = []
        resource_states += self.node_system.res_state_many(resource_list, include_node=include_node)
        if not remote:
            for node in self.remote_systems:
                resource_states += self.remote_systems[node].clus_res_state_many(resource_list,
                                                                                 include_node=include_node,
                                                                                 remote=True)
        return resource_states

    @Pyro.expose
    def clus_res_link(self, parent_name, resource_name, remote=False):
        """Add a resource dependency on the cluster"""
        self.node_system.res_link(parent_name, resource_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_res_link(parent_name, resource_name, remote=True)

    @Pyro.expose
    def clus_res_unlink(self, parent_name, resource_name, remote=False):
        """Remove a resource dependency on the cluster"""
        self.node_system.res_unlink(parent_name, resource_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_res_unlink(parent_name, resource_name, remote=True)

    @Pyro.expose
    def clus_res_clear(self, resource_name, remote=False):
        self.node_system.res_clear(resource_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_res_clear(resource_name, remote=True)

    @Pyro.expose
    def clus_res_probe(self, resource_name):
        return self.node_system.res_probe(resource_name)

    @Pyro.expose
    def clus_res_dep(self, resource_args):
        return self.node_system.res_dep(resource_args)

    @Pyro.expose
    def clus_res_list(self):
        return self.node_system.res_list()

    @Pyro.expose
    def clus_res_value(self, resource_name, attr_name):
        return self.node_system.res_value(resource_name, attr_name)

    @Pyro.expose
    def clus_res_modify(self, resource_name, attr_name, value, remote=False):
        """Modify a resource attribute on the cluster"""
        self.node_system.res_modify(resource_name, attr_name, value)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_res_modify(resource_name, attr_name, value, remote=True)

    @Pyro.expose
    def clus_res_attr(self, resource_name):
        return self.node_system.res_attr(resource_name)

    @Pyro.expose
    def clus_grp_online(self, group_name, system_name):
        """Online group for a given system node"""
        if self.node_system.attr_value('NodeName') == system_name:
            # TODO: check if online on other node first
            self.node_system.grp_online(group_name)
        else:
            self.remote_systems[system_name].clus_grp_online(group_name, system_name)

    @Pyro.expose
    def clus_grp_offline(self, group_name, system_name):
        """Offline group for a given system node"""
        if self.node_system.attr_value('NodeName') == system_name:
            self.node_system.grp_offline(group_name)
        else:
            self.remote_systems[system_name].clus_grp_offline(group_name, system_name)

    @Pyro.expose
    def clus_grp_state(self, group_name):
        return self.node_system.grp_state(group_name)

    @Pyro.expose
    def clus_grp_state_many(self, group_list, include_node=False, remote=False):
        """Provide states for given group names for all nodes in cluster"""
        group_states = []
        group_states += self.node_system.grp_state_many(group_list, include_node=include_node)
        if not remote:
            for node in self.remote_systems:
                group_states += self.remote_systems[node].clus_grp_state_many(group_list, include_node=include_node,
                                                                              remote=True)
        return group_states

    @Pyro.expose
    def clus_grp_add(self, group_name, remote=False):
        """Add a group to the cluster"""
        self.node_system.grp_add(group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_add(group_name, remote=True)

    @Pyro.expose
    def clus_grp_delete(self, group_name, remote=False):
        """Remove a group from the cluster"""
        self.node_system.grp_delete(group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_delete(group_name, remote=True)

    @Pyro.expose
    def clus_grp_enable(self, group_name, remote=False):
        """Enable a group on the cluster"""
        self.node_system.grp_enable(group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_enable(group_name, remote=True)

    @Pyro.expose
    def clus_grp_disable(self, group_name, remote=False):
        """Disable a group on the cluster"""
        self.node_system.grp_disable(group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_disable(group_name, remote=True)

    @Pyro.expose
    def clus_grp_enable_resources(self, group_name, remote=False):
        """Enable a group resources on a cluster"""
        self.node_system.grp_enable_resources(group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_enable_resources(group_name, remote=True)

    @Pyro.expose
    def clus_grp_disable_resources(self, group_name, remote=False):
        """Disable a group resources on a cluster"""
        self.node_system.grp_disable_resources(group_name)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_disable_resources(group_name, remote=True)

    @Pyro.expose
    def clus_grp_flush(self, group_name, system_name):
        """Flush a group on the cluster"""
        if system_name == self.node_name:
            self.node_system.grp_flush(group_name)
        else:
            self.remote_systems[system_name].clus_grp_flush(group_name, system_name)

    @Pyro.expose
    def clus_grp_clear(self, group_name, system_name):
        """Clear a group on the cluster"""
        if system_name == self.node_name:
            self.node_system.grp_clear(group_name)
        else:
            self.remote_systems[system_name].clus_grp_clear(group_name, system_name)

    @Pyro.expose
    def clus_grp_resources(self, group_name):
        """List a group resources on the cluster"""
        return self.node_system.grp_resources(group_name)

    @Pyro.expose
    def clus_grp_list(self):
        """List groups on the cluster"""
        return self.node_system.grp_list()

    @Pyro.expose
    def clus_grp_value(self, group_name, attr_name):
        """Get a value from a group on the cluster"""
        return self.node_system.grp_value(group_name, attr_name)

    @Pyro.expose
    def clus_grp_modify(self, group_name, attr_name, value, remote=False):
        """Modify a group attribute value on the cluster"""
        self.node_system.grp_modify(group_name, attr_name, value)
        if not remote:
            for node in self.remote_systems:
                self.remote_systems[node].clus_grp_modify(group_name, attr_name, value, remote=True)

    @Pyro.expose
    def clus_grp_attr(self, group_name):
        """Get group attribute values from the cluster"""
        return self.node_system.grp_attr(group_name)
