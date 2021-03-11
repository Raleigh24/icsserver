import unittest

import Pyro4 as Pyro

import ics.errors
import ics.states
from ics.resource import Group
from ics.resource import Resource
from ics.system import NodeSystem


class TestNodeSystem(unittest.TestCase):

    def setUp(self) -> None:
        self.system = NodeSystem()

    def setup_simple_group(self):
        resource_list = ['proc_a1', 'proc_a2', 'proc_a3']
        group_name = 'group_a'
        self.system.grp_add(group_name)
        for resource_name in resource_list:
            self.system.res_add(resource_name, group_name)

    @unittest.skip('Need to setup server first.')
    def test_ping(self):
        self.fail()

    def test_register_node(self):
        self.system.register_node('test_host')
        self.assertNotEqual(self.system.remote_nodes, {})
        self.assertIsInstance(self.system.remote_nodes['test_host'], Pyro.core.Proxy)

    def test_add_node(self):
        self.system.add_node('test_host')
        self.assertNotEqual(self.system.remote_nodes, {})
        self.assertIsInstance(self.system.remote_nodes['test_host'], Pyro.core.Proxy)
        self.assertEqual(self.system.attr_value('NodeList'), ['test_host'])

    def test_delete_node(self):
        self.system.add_node('test_host')
        self.system.add_node('test_host2')
        self.system.delete_node('test_host')
        with self.assertRaises(KeyError):
            test_val = self.system.remote_nodes['test_host']

        self.assertEqual(['test_host2'], self.system.attr_value('NodeList'))

    @unittest.skip
    def test_heartbeat(self):
        self.fail()

    @unittest.skip
    def test_clus_res_online(self):
        self.fail()

    @unittest.skip
    def test_clus_res_offline(self):
        self.fail()

    @unittest.skip
    def test_clus_res_add(self):
        self.fail()

    @unittest.skip
    def test_clus_res_delete(self):
        self.fail()

    @unittest.skip
    def test_clus_res_state(self):
        self.fail()

    @unittest.skip
    def test_clus_res_state_many(self):
        self.fail()

    @unittest.skip
    def test_clus_res_link(self):
        self.fail()

    @unittest.skip
    def test_clus_res_unlink(self):
        self.fail()

    @unittest.skip
    def test_clus_res_clear(self):
        self.fail()

    @unittest.skip
    def test_clus_res_probe(self):
        self.fail()

    @unittest.skip
    def test_clus_res_dep(self):
        self.fail()

    @unittest.skip
    def test_clus_res_list(self):
        self.fail()

    @unittest.skip
    def test_clus_res_value(self):
        self.fail()

    @unittest.skip
    def test_clus_res_modify(self):
        self.fail()

    @unittest.skip
    def test_clus_res_attr(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_online(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_offline(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_state(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_state_all(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_add(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_delete(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_enable(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_disable(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_enable_resources(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_disable_resources(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_flush(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_clear(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_resources(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_list(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_value(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_modify(self):
        self.fail()

    @unittest.skip
    def test_clus_grp_attr(self):
        self.fail()

    def test_set_attr(self):
        self.system.set_attr('ResourceLimit', '12345')
        self.assertEqual(self.system.attr_value('ResourceLimit'), '12345')

    def test_set_attr_cluster_name(self):
        test_cluster_name = 'cluster_1'
        self.system.set_attr('ClusterName', test_cluster_name)
        self.assertEqual(self.system.cluster_name, test_cluster_name)
        self.assertEqual(self.system.attr_value('ClusterName'), test_cluster_name)

    def test_set_attr_node_name(self):
        test_node_name = 'cluster_1'
        self.system.set_attr('NodeName', test_node_name)
        self.assertEqual(self.system.node_name, test_node_name)
        self.assertEqual(self.system.attr_value('NodeName'), test_node_name)

    def test_node_attr(self):
        self.assertIsInstance(self.system.node_attr(), list)

    def test_node_value(self):
        self.system.set_attr('ResourceLimit', '12345')
        self.assertEqual(self.system.node_value('ResourceLimit'), '12345')

    def test_node_modify(self):
        self.system.node_modify('ResourceLimit', '12345')
        self.assertEqual(self.system.attr_value('ResourceLimit'), '12345')

    def test_get_resource(self):
        self.setup_simple_group()
        resource = self.system.get_resource('proc_a1')
        self.assertIsInstance(resource, Resource)
        self.assertEqual(resource.name, 'proc_a1')

    def test_get_resource_invalid(self):
        resource_name = 'proc_a99'
        with self.assertRaises(ics.errors.ICSError):
            self.system.get_resource(resource_name)

    @unittest.skip('Need to setup server first.')
    def test_res_online(self):
        self.fail()

    def test_res_online_monitor_only(self):
        self.setup_simple_group()
        self.system.res_modify('proc_a1', 'MonitorOnly', 'true')
        with self.assertRaises(ics.errors.ICSError):
            self.system.res_online('proc_a1')

    @unittest.skip('Need to setup server first.')
    def test_res_offline(self):
        self.fail()

    def test_res_add(self):
        resource_name = 'proc_a1'
        group_name = 'group_a'

        # Test when group does not exist yet
        with self.assertRaises(ics.errors.ICSError):
            self.system.res_add(resource_name, group_name)

        self.system.grp_add(group_name)
        self.system.res_add(resource_name, group_name)
        self.assertIsInstance(self.system.resources[resource_name], Resource)

        # Test when resource already exists
        with self.assertRaises(ics.errors.ICSError):
            self.system.res_add(resource_name, group_name)

    def test_res_delete(self):
        self.setup_simple_group()
        resource_name = 'proc_a1'
        group_name = 'group_a'
        self.system.res_delete(resource_name)

        self.assertNotIn(resource_name, self.system.resources)
        self.assertNotIn(resource_name, self.system.groups[group_name].members)

        with self.assertRaises(ics.errors.ICSError):
            self.system.res_delete(resource_name)

    def test_res_delete_invalid(self):
        self.setup_simple_group()
        with self.assertRaises(ics.errors.ICSError):
            self.system.res_delete('proc_a99')

    def test_res_state(self):
        resource_name = 'proc_a1'
        group_name = 'group_a'
        self.system.grp_add(group_name)
        self.system.res_add(resource_name, group_name, init_state=ics.states.ResourceStates.ONLINE)
        self.assertEqual(self.system.res_state(resource_name), 'ONLINE')

    def test_res_state_many(self):
        resource_list = ['proc_a1', 'proc_a2']
        group_name = 'group_a'
        resource_states = [['proc_a1', 'OFFLINE'], ['proc_a2', 'OFFLINE']]
        resource_states_node = [['proc_a1', 'node_1', 'OFFLINE'], ['proc_a2', 'node_1', 'OFFLINE']]
        self.system.set_attr('NodeName', 'node_1')
        self.system.grp_add(group_name)
        for resource_name in resource_list:
            self.system.res_add(resource_name, group_name, init_state=ics.states.ResourceStates.OFFLINE)

        self.assertEqual(self.system.res_state_many(resource_list), resource_states)
        self.assertEqual(self.system.res_state_many(resource_list, include_node=True), resource_states_node)

    def test_res_link(self):
        self.setup_simple_group()
        self.system.res_link('proc_a2', 'proc_a1')
        self.system.res_link('proc_a3', 'proc_a1')

        resource = self.system.get_resource('proc_a2')
        self.assertEqual(resource.dependencies(), ['proc_a1'])
        resource = self.system.get_resource('proc_a3')
        self.assertEqual(resource.dependencies(), ['proc_a1'])

    def test_res_unlink(self):
        self.setup_simple_group()
        self.system.res_link('proc_a2', 'proc_a1')
        self.system.res_link('proc_a3', 'proc_a1')

        self.system.res_unlink('proc_a2', 'proc_a1')
        resource = self.system.get_resource('proc_a2')
        self.assertEqual(resource.dependencies(), [])
        resource = self.system.get_resource('proc_a3')
        self.assertEqual(resource.dependencies(), ['proc_a1'])

    def test_res_dep(self):
        self.setup_simple_group()
        self.system.res_link('proc_a2', 'proc_a1')
        self.system.res_link('proc_a3', 'proc_a1')
        dep_list = [['group_a', 'proc_a1', 'proc_a2'], ['group_a', 'proc_a1', 'proc_a3']]
        self.assertEqual(self.system.res_dep(['proc_a1']), dep_list)

    def test_res_dep_many(self):
        self.setup_simple_group()
        self.system.res_link('proc_a2', 'proc_a1')
        self.system.res_link('proc_a3', 'proc_a1')
        dep_list = [['group_a', 'proc_a1', 'proc_a2'], ['group_a', 'proc_a1', 'proc_a3']]
        self.assertEqual(self.system.res_dep(['proc_a1']), dep_list)

    @unittest.skip('Need to setup server first.')
    def test_res_clear(self):
        self.fail()

    @unittest.skip('Need to setup server first.')
    def test_res_probe(self):
        self.fail()

    def test_res_list(self):
        resource_list = ['proc_a1', 'proc_a2', 'proc_a3']
        self.assertEqual(self.system.res_list(), [])
        self.setup_simple_group()
        self.assertEqual(self.system.res_list(), resource_list)

    def test_res_value(self):
        self.setup_simple_group()
        self.assertEqual(self.system.res_value('proc_a1', 'Enabled'), 'false')

    def test_res_modify(self):
        self.setup_simple_group()
        self.system.res_modify('proc_a1', 'Enabled', 'true')
        self.assertEqual(self.system.res_value('proc_a1', 'Enabled'), 'true')

    def test_res_attr(self):
        self.setup_simple_group()
        self.assertIsInstance(self.system.res_attr('proc_a1'), list)

    def test_get_group(self):
        self.setup_simple_group()
        group = self.system.get_group('group_a')
        self.assertIsInstance(group, Group)
        self.assertEqual(group.name, 'group_a')

    def test_get_group_invalid(self):
        with self.assertRaises(ics.errors.ICSError):
            self.system.get_group('group_a')

    @unittest.skip('Need to setup server first.')
    def test_grp_online(self):
        self.fail()

    @unittest.skip('Need to setup server first.')
    def test_grp_online_auto(self):
        self.fail()

    @unittest.skip('Need to setup server first.')
    def test_grp_offline(self):
        self.fail()

    @unittest.skip('Need to setup server first.')
    def test_grp_state(self):
        self.fail()

    def test_grp_add(self):
        group_name = 'group_a'
        self.system.grp_add(group_name)
        self.assertIsInstance(self.system.groups[group_name], Group)

        # Test when resource already exists
        with self.assertRaises(ics.errors.ICSError):
            self.system.grp_add(group_name)

    def test_grp_delete(self):
        self.setup_simple_group()
        self.system.res_delete('proc_a1')  # Needs to be removed before group can be deleted
        self.system.grp_delete('group_a')
        self.assertNotIn('group_a', self.system.resources)

    def test_grp_enable(self):
        self.setup_simple_group()
        self.system.grp_enable('group_a')
        self.assertEqual(self.system.grp_value('group_a', 'Enabled'), 'true')

    def test_grp_disable(self):
        self.setup_simple_group()
        self.system.grp_disable('group_a')
        self.assertEqual(self.system.grp_value('group_a', 'Enabled'), 'false')

    def test_grp_enable_resources(self):
        self.setup_simple_group()
        self.system.grp_enable_resources('group_a')
        for resource_name in self.system.grp_resources('group_a'):
            self.assertEqual(self.system.res_value(resource_name, 'Enabled'), 'true')

    def test_grp_disable_resources(self):
        self.setup_simple_group()
        self.system.grp_disable_resources('group_a')
        for resource_name in self.system.grp_resources('group_a'):
            self.assertEqual(self.system.res_value(resource_name, 'Enabled'), 'false')

    @unittest.skip('Need to setup server first.')
    def test_grp_flush(self):
        self.fail()

    @unittest.skip('Need to setup server first.')
    def test_grp_clear(self):
        self.fail()

    def test_grp_resources(self):
        self.setup_simple_group()
        self.assertEqual(self.system.grp_resources('group_a'), ['proc_a1', 'proc_a2', 'proc_a3'])

    def test_grp_list(self):
        self.setup_simple_group()
        self.assertEqual(self.system.grp_list(), ['group_a'])

    def test_grp_value(self):
        self.setup_simple_group()
        self.assertEqual(self.system.grp_value('group_a', 'Enabled'), 'false')

    def test_grp_modify(self):
        self.setup_simple_group()
        self.system.grp_modify('group_a', 'Enabled', 'true')
        self.assertEqual(self.system.grp_value('group_a', 'Enabled'), 'true')

    def test_grp_attr(self):
        self.setup_simple_group()
        self.assertIsInstance(self.system.grp_attr('group_a'), list)

    def test_load_default(self):
        self.setup_simple_group()
        self.assertEqual(self.system.load(), 0)

    def test_load(self):
        self.setup_simple_group()
        resource = self.system.get_resource('proc_a1')
        resource.state = ics.states.ResourceStates.ONLINE
        resource = self.system.get_resource('proc_a2')
        resource.state = ics.states.ResourceStates.ONLINE
        self.assertEqual(self.system.load(), 2)

    @unittest.skip
    def test_poll_updater(self):
        self.fail()

    @unittest.skip
    def test_poll_count(self):
        self.fail()

    @unittest.skip
    def test_startup_poll(self):
        self.fail()

    @unittest.skip
    def test_start_event_handler(self):
        self.fail()

    @unittest.skip
    def test_start_poll_updater(self):
        self.fail()

    @unittest.skip
    def test_start_threads(self):
        self.fail()

    @unittest.skip
    def test_config_data(self):
        self.fail()

    @unittest.skip
    def test_load_config(self):
        self.fail()

    @unittest.skip
    def test_backup_config(self):
        self.fail()

    @unittest.skip
    def test_startup(self):
        self.fail()

    @unittest.skip
    def test_run(self):
        self.fail()

    @unittest.skip
    def test_shutdown(self):
        self.fail()


if __name__ == "__main__":
    unittest.main()
