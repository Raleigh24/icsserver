import logging
import logging.config
import signal
import sys
import os
import socket

import Pyro4 as Pyro

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
    logging.config.fileConfig(ICS_HOME + '/etc/logging.conf')
except IOError as e:
    print('ERROR: Unable to create log file: {}'.format(e))
    sys.exit(1)

from cluster import Cluster  # Not sure why this needs to be here

# Setup logging information
logger = logging.getLogger(__name__)


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

logger.info('Starting ICS server...')
logger.info('ICS Version: ' + ICS_VERSION)
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

system = Cluster()

logging.getLogger("Pyro4").setLevel(logging.INFO)
logging.getLogger("Pyro4.core").setLevel(logging.INFO)

system.startup()
#system.cluster_connect()
#system.run()  # Run forever

Pyro.Daemon.serveSimple(
    {
        system: 'system'
    },
    port=9090,
    host=socket.gethostname(),
    ns=False)

