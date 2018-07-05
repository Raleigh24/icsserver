import logging
import logging.config
import signal
import sys
import threading
import time
import os

from environment import ICS_VERSION
from environment import ICS_HOME
from environment import ICS_LOG

# Need to create logger before importing other modules
if not os.path.isdir(ICS_LOG):
    try:
        os.makedirs(ICS_LOG)
    except OSError as e:
        print('ERROR: Unable to create log directory: {}'.format(e))
        print('Exiting...')
        exit(1)
# TODO: Check if file path exists
logging.logFilename = ICS_LOG + '/icsserver.log'
try:
    logging.config.fileConfig(ICS_HOME + '/ics/logging.conf')
except IOError as e:
    print('ERROR: Unable to create log file: {}'.format(e))
    exit(1)

import config
import network
from resource import poll_updater
from events import event_handler
from rpcinterface import rpc_runner
from custom_exceptions import NetworkError

# Setup logging information
logger = logging.getLogger(__name__)


# Set up signal handling
def signal_handler(signal_code, frame):
    if signal_code is signal.SIGINT:
        logging.critical('Caught signal SIGINT (Ctrl + C), exiting...')
        config.save_config()
        # TODO: gracefully shutdown
    elif signal_code is signal.SIGTERM:
        logging.debug('SIGTERM line at {}'.format(frame.f_lineno))
        logging.critical('Caught signal SIGTERM, exiting...')
        config.save_config()
        # TODO: gracefully shutdown
    exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

logger.info('Starting ICS server...')
logger.info('ICS Version: ' + ICS_VERSION)
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

# Initialize server from configuration file
config.load_config()

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
except NetworkError:
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
    config.save_config()
