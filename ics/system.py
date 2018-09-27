import threading
import logging
import time

import network
from resource import Node
from events import event_handler
from rpcinterface import rpc_runner
from custom_exceptions import NetworkError, SystemError


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

        # Start client handler thread
        logger.info('Starting client handler...')
        try:
            sock = network.create_tcp_interface()
        except NetworkError:
            logger.critical('Unable to create client interface, exiting...')
            raise SystemError
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
            self.node.grp_list
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
        logger.info('Server startup complete')

    def run(self):
        while True:
            for thread in self.threads:
                if not thread.is_alive():
                    logger.critical('Thread {} no longer running'.format(thread.name))
                    #thread.start()  # Attempt to restart thread
            time.sleep(5)

    def shutdown(self):
        # for thread in self.threads:
        #     thread_name = thread.name
        #     thread.set()
        #
        # for thread in self.threads:
        #     thread.join()
        #TODO: save config
        pass



