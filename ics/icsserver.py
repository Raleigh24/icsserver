import logging
import signal
import sys
import threading
import time
import os

import config
config.create_logger()  # Need to create logger before importing other modules
import network
from resource import poll_updater, load_config, save_config
from events import event_handler
from rpcinterface import rpc_runner
from custom_exceptions import NetworkConnectionError


# Setup logging information
logger = logging.getLogger(__name__)


# Set up signal handling
def signal_handler(signal_code, frame):
    if signal_code is signal.SIGINT:
        logging.critical('Caught signal SIGINT (Ctrl + C), exiting...')
        save_config(config.RES_CONF)
        # TODO: gracefully shutdown
    elif signal_code is signal.SIGTERM:
        logging.debug('SIGTERM line at {}'.format(frame.f_lineno))
        logging.critical('Caught signal SIGTERM, exiting...')
        save_config(config.RES_CONF)
        # TODO: gracefully shutdown
    exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

logger.info('Starting ICS server...')
logger.info('ICS Version: ' + config.ICS_VERSION)
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

# Initialize resources
logger.info('Loading from config file')
if not os.path.isfile(config.RES_CONF):
    logger.info('No config file found, skipping load')
else:
    load_config(config.RES_CONF)

threads = []

# Start event handler thread
logger.info('Starting event handler...')
thread_event_handler = threading.Thread(name='event handler', target=event_handler)
thread_event_handler.daemon = True
thread_event_handler.start()
threads.append(thread_event_handler)

# Start client handler thread
logger.info('Starting client handler...')
try:
    sock = network.create_tcp_interface()
except NetworkConnectionError:
    logger.critical('Unable to create client interface, exiting...')
    exit(1)
thread_client_handler = threading.Thread(name='client handler', target=network.handle_clients, args=(sock,))
thread_client_handler.daemon = True
thread_client_handler.start()
threads.append(thread_client_handler)

# Start poll updater thread
logger.info('Starting poll updater...')
thread_poll_updater = threading.Thread(name='poll updater', target=poll_updater)
thread_poll_updater.daemon = True
thread_poll_updater.start()
threads.append(thread_poll_updater)

# Start RPC interface thread
logger.info('Starting RPC interface...')
thread_rpc_interface = threading.Thread(name='RPC interface', target=rpc_runner)
thread_rpc_interface.daemon = True
thread_rpc_interface.start()
threads.append(thread_rpc_interface)

logger.info('Server startup complete')

while True:
    for thread in threads:
        if not thread.is_alive():
            logger.critical('Thread {} no longer running'.format(thread.name))

    time.sleep(5)
    save_config(config.RES_CONF)
