import logging
import logging.config
import os
import signal
import socket
import sys

import Pyro4 as Pyro

from environment import ICS_ENGINE_PORT
from environment import ICS_LOG
from ics import utils
from system import NodeSystem

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
    log_config = os.path.dirname(__file__) + '/logging_console.conf'
else:
    log_config = os.path.dirname(__file__) + '/logging.conf'

try:
    logging.config.fileConfig(log_config, disable_existing_loggers=False)
except IOError as e:
    print('ERROR: Unable to create log file: {}'.format(e))
    sys.exit(1)

# Setup logging information
logger = logging.getLogger('main')
logger.info('Starting ICS server...')
logger.info('ICS Version: ' + utils.ics_version())
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))
logger.info('Logging config:' + log_config)

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
system.run()  # Run forever

logger.info("Starting Pyro on port " + str(ICS_ENGINE_PORT))

Pyro.Daemon.serveSimple(
    {
        system: 'system'
    },
    port=ICS_ENGINE_PORT,
    host=socket.gethostname(),
    ns=False,
    verbose=False)

