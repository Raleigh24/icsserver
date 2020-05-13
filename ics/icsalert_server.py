import logging
import logging.config
import signal
import sys
import os
import socket
import threading

import Pyro4 as Pyro

from alerts import AlertHandler
from environment import ICS_VERSION
from environment import ICS_HOME
from environment import ICS_LOG
from environment import ICS_ALERT_PORT

if not os.path.isdir(ICS_LOG):
    try:
        os.makedirs(ICS_LOG)
    except OSError as e:
        print('ERROR: Unable to create log directory: {}'.format(e))
        print('Exiting...')
        sys.exit(1)

# TODO: Check if file path exists
logging.logFilename = ICS_LOG + '/icsserver_alert.log'
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
logger.info('Starting ICS alert server...')
logger.info('ICS Version: ' + ICS_VERSION)
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

# Setup Pyro logging
logging.getLogger("Pyro4").setLevel(logging.INFO)
logging.getLogger("Pyro4.core").setLevel(logging.INFO)

alert_handler = AlertHandler()

# Start alert handler thread
logger.info('Starting alert handler...')
thread_alert_handler = threading.Thread(name='alert handler', target=alert_handler.run)
thread_alert_handler.daemon = True
thread_alert_handler.start()

logger.info("Starting Pyro on port " + str(ICS_ALERT_PORT))

Pyro.Daemon.serveSimple(
    {
        alert_handler: 'alert_handler'
    },
    port=ICS_ALERT_PORT,
    host=socket.gethostname(),
    ns=False,
    verbose=False)






