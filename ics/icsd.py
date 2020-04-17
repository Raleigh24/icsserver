import logging.config
import sys
import os
import socket

import Pyro4 as Pyro

import utils
from environment import ICS_HOME
from environment import ICS_LOG
from environment import ICS_VERSION
from server_control import SubServerControl

if not os.path.isdir(ICS_LOG):
    try:
        os.makedirs(ICS_LOG)
    except OSError as e:
        print('ERROR: Unable to create log directory: {}'.format(e))
        print('Exiting...')
        sys.exit(1)

logging.logFilename = ICS_LOG + '/icsd.log'
if os.getenv('ICS_CONSOLE_LOG') is not None:
    log_config = ICS_HOME + '/etc/logging_console.conf'
else:
    log_config = ICS_HOME + '/etc/logging.conf'

try:
    logging.config.fileConfig(log_config)
except IOError as e:
    print('ERROR: Unable to create log file: {}'.format(e))
    sys.exit(1)

logger = logging.getLogger('main')
logger.info('Starting ICS daemon...')
logger.info('ICS Version: ' + ICS_VERSION)
logger.info('Python version: ' + sys.version.replace('\n', ''))
logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

# Setup Pyro logging
logging.getLogger("Pyro4").setLevel(logging.INFO)
logging.getLogger("Pyro4.core").setLevel(logging.INFO)

utils.setup_signal_handler()

sub_server_control = SubServerControl()

Pyro.Daemon.serveSimple(
    {
        sub_server_control: 'sub_server_control'
    },
    port=9091,
    host=socket.gethostname(),
    ns=False,
    verbose=False)
