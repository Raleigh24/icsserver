import threading
import logging
import time
import sys
import os

import network
from resource import Node
from events import event_handler
from alerts import AlertHandler
from rpcinterface import rpc_runner
from ics_exceptions import ICSError
from utils import set_log_level, read_json, write_json
from environment import ICS_CONF_FILE

logger = logging.getLogger(__name__)


class System:

    def __init__(self):
        self.threads = []
        self.node = Node()
        self.alert_handler = AlertHandler()

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
        thread_poll_updater = threading.Thread(name='poll updater', target=self.node.poll_updater)
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
            self.node.node_attr,
            self.node.node_value,
            self.node.node_modify,
            self.node.res_online,
            self.node.res_offline,
            self.node.res_add,
            self.node.res_delete,
            self.node.res_state,
            self.node.res_clear,
            self.node.res_probe,
            self.node.res_dep,
            self.node.res_list,
            self.node.res_link,
            self.node.res_unlink,
            self.node.res_value,
            self.node.res_modify,
            self.node.res_attr,
            self.node.grp_online,
            self.node.grp_offline,
            self.node.grp_add,
            self.node.grp_delete,
            self.node.grp_enable,
            self.node.grp_disable,
            self.node.grp_state,
            self.node.grp_flush,
            self.node.grp_clear,
            self.node.grp_resources,
            self.node.grp_list,
            self.node.grp_value,
            self.node.grp_modify,
            self.node.grp_attr,
            self.alert_handler.add_recipient,
            self.alert_handler.remove_recipient
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
            'system': {'attributes': self.node.modified_attributes()},
            'alerts': {'attributes': {
                'AlertLevel': self.alert_handler.get_level(), 'AlertRecipients': self.alert_handler.recipients},
            },
            'groups': {},
            'resources': {}
        }

        for group in self.node.groups.values():
            config_data['groups'][group.name] = {'attributes': group.modified_attributes()}
        for resource in self.node.resources.values():
            config_data['resources'][resource.name] = {'attributes': resource.modified_attributes(),
                                                       'dependencies': resource.dependencies()}
        return config_data

    def load_config(self, filename):
        logger.info('Loading configuration...')
        if not os.path.isfile(filename):
            logger.info('No config found, skipping load')
            return

        try:
            data = read_json(filename)
        except ValueError as error:
            logging.error('Error occurred while loading config: {}'.format(str(error)))
            return

        try:
            # Set system attributes from config
            system_data = data['system']
            for attr_name in system_data['attributes']:
                self.node.set_attr(attr_name, system_data['attributes'][attr_name])

            # Set alert attributes from config
            alert_data = data['alerts']
            self.alert_handler.set_level(alert_data['attributes']['AlertLevel'])
            for recipient in alert_data['attributes']['AlertRecipients']:
                self.alert_handler.add_recipient(recipient)

            # Create groups from config
            group_data = data['groups']
            for group_name in group_data:
                group = self.node.grp_add(group_name)
                for attr_name in group_data[group_name]['attributes']:
                    group.set_attr(attr_name, str(group_data[group_name]['attributes'][attr_name]))

            # Create resources from config
            resource_data = data['resources']
            for resource_name in resource_data.keys():
                group_name = resource_data[resource_name]['attributes']['Group']
                resource = self.node.res_add(resource_name, group_name)
                for attr_name in resource_data[resource_name]['attributes']:
                    resource.set_attr(attr_name, str(resource_data[resource_name]['attributes'][attr_name]))

            # Create resource dependency links
            # Note: Links need to be done in separate loop to guarantee parent resources
            # are created first when establishing links
            for resource_name in resource_data.keys():
                for dep_name in resource_data[resource_name]['dependencies']:
                    self.node.res_link(dep_name, resource_name)
        except (TypeError, KeyError) as error:
            logging.error('Error occurred while loading config: {}:{}'.format(error.__class__.__name__, str(error)))
            raise

    def write_config(self, filename):
        """Write configuration to file"""
        data = self.config_data()
        write_json(filename, data)

    def backup_config(self):
        while True:
            interval = int(self.node.attr_value('BackupInterval'))
            if interval != 0:
                logging.debug('Creating backup of config file')
                if os.path.isfile(ICS_CONF_FILE):
                    os.rename(ICS_CONF_FILE, ICS_CONF_FILE + '.autobackup')
                self.write_config(ICS_CONF_FILE)
                time.sleep(interval * 60)
            else:
                time.sleep(60)

    def startup(self):
        logger.info('Server starting up...')
        # TODO: Add config_dict startup management here
        try:
            self.load_config(ICS_CONF_FILE)
        except Exception as e:
            logging.critical('Error reading config file: {}'.format(str(e)))
            sys.exit(1)  # TODO: better system handling
        self.start_threads()
        self.node.grp_online_auto()
        # TODO: start polling updater
        logger.info('Server startup complete')

    def run(self):
        while True:
            for thread in self.threads:
                if not thread.is_alive():
                    logger.critical('Thread {} no longer running'.format(thread.name))
                    #thread.start()  # Attempt to restart thread
            time.sleep(5)

    def shutdown(self):
        logging.info('Server shutting down...')
        # for thread in self.threads:
        #     thread_name = thread.name
        #     thread.set()
        #
        # for thread in self.threads:
        #     thread.join()
        self.write_config(ICS_CONF_FILE)
        logging.info('Server shutdown complete')
        logging.shutdown()



