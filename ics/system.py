import threading
import logging
import time

import network
from resource import Node
from events import event_handler
from alerts import alert_handler
from rpcinterface import rpc_runner
from ics_exceptions import ICSError
from utils import set_log_level
from environment import ICS_CONF_FILE

logger = logging.getLogger(__name__)


class System:

    def __init__(self):
        self.threads = []
        self.node = None

    def start_threads(self):
        # Start event handler thread
        logger.info('Starting event handler...')
        thread_event_handler = threading.Thread(name='event handler', target=event_handler)
        thread_event_handler.daemon = True
        thread_event_handler.start()
        self.threads.append(thread_event_handler)

        # Start alert handler thread
        logger.info('Starting alert handler...')
        thread_event_handler = threading.Thread(name='alert handler', target=alert_handler)
        thread_event_handler.daemon = True
        thread_event_handler.start()
        self.threads.append(thread_event_handler)

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
        thread_config_backup = threading.Thread(name='backup config', target=self.node.backup_config)
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
            self.node.grp_attr
        ]

        # Start RPC interface thread
        logger.info('Starting RPC interface...')
        thread_rpc_interface = threading.Thread(name='RPC interface', target=rpc_runner, args=(rpc_function_list,))
        thread_rpc_interface.daemon = True
        thread_rpc_interface.start()
        self.threads.append(thread_rpc_interface)

    def startup(self):
        logger.info('Server starting up...')
        self.node = Node()
        #TODO: Add config startup management here
        self.node.load_config()
        self.start_threads()
        self.node.grp_online_auto()
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
        self.node.write_config(ICS_CONF_FILE)
        logging.info('Server shutdown complete')
        logging.shutdown()



