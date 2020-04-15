import logging
import logging.config
import signal
import sys
import os
import socket

import Pyro4 as Pyro

from system import NodeSystem
from environment import ICS_VERSION
from environment import ICS_HOME
from environment import ICS_LOG

if not os.path.isdir(ICS_LOG):
    try:
        os.makedirs(ICS_LOG)
    except OSError as e:
        print('ERROR: Unable to create log directory: {}'.format(e))
        print('Exiting...')
        sys.exit(1)

# TODO: Check if file path exists
logging.logFilename = ICS_LOG + '/icsserver.log'
if os.getenv('ICS_CONSOLE_LOG') is not None:
    log_config = ICS_HOME + '/etc/logging_console.conf'
else:
    log_config = ICS_HOME + '/etc/logging.conf'

try:
    logging.config.fileConfig(log_config)
except IOError as e:
    print('ERROR: Unable to create log file: {}'.format(e))
    sys.exit(1)

# Setup logging information
logger = logging.getLogger('main')
logger.info('Starting ICS server...')
logger.info('ICS Version: ' + ICS_VERSION)
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

# Setup Pyro logging
logging.getLogger("Pyro4").setLevel(logging.INFO)
logging.getLogger("Pyro4.core").setLevel(logging.INFO)

system = NodeSystem()

# Set up signal handling
def signal_handler(signal_code, frame):
    if signal_code is signal.SIGINT:
        logging.critical('Caught signal SIGINT (Ctrl + C), exiting...')
        system.shutdown()
        # TODO: gracefully shutdown
    elif signal_code is signal.SIGTERM:
        logging.debug('SIGTERM line at {}'.format(frame.f_lineno))
        logging.critical('Caught signal SIGTERM, exiting...')
        system.shutdown()
        # TODO: gracefully shutdown
    sys.exit(1)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

system.startup()
#system.cluster_connect()
#system.run()  # Run forever

Pyro.Daemon.serveSimple(
    {
        system: 'system'
    },
    port=9090,
    host=socket.gethostname(),
    ns=False,
    verbose=False)

