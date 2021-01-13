import logging.config
import os
import socket
import sys

import Pyro4 as Pyro

from ics import utils
from ics.environment import ICS_DAEMON_PORT
from ics.environment import ICS_LOG
from ics.server_control import SubServerControl


def main():
    if not os.path.isdir(ICS_LOG):
        try:
            os.makedirs(ICS_LOG)
        except OSError as e:
            print('ERROR: Unable to create log directory: {}'.format(e))
            print('Exiting...')
            sys.exit(1)

    logging.logFilename = ICS_LOG + '/icsd.log'
    if os.getenv('ICS_CONSOLE_LOG') is not None:
        log_config = os.path.dirname(__file__) + '/logging_console.conf'
    else:
        log_config = os.path.dirname(__file__) + '/logging.conf'

    try:
        logging.config.fileConfig(log_config)
    except IOError as e:
        print('ERROR: Unable to create log file: {}'.format(e))
        sys.exit(1)

    logger = logging.getLogger('main')
    logger.info('Starting ICS daemon...')
    logger.info('ICS Version: ' + utils.ics_version())
    logger.info('Python version: ' + sys.version.replace('\n', ''))
    logger.info('Logging level: ' + logging.getLevelName(logger.getEffectiveLevel()))

    # Setup Pyro logging
    logging.getLogger("Pyro4").setLevel(logging.INFO)
    logging.getLogger("Pyro4.core").setLevel(logging.INFO)

    utils.setup_signal_handler()

    sub_server_control = SubServerControl()

    logger.info("Starting Pyro on port " + str(ICS_DAEMON_PORT))

    Pyro.Daemon.serveSimple(
        {
            sub_server_control: 'sub_server_control'
        },
        port=ICS_DAEMON_PORT,
        host=socket.gethostname(),
        ns=False,
        verbose=False)


if __name__ == '__main__':
    main()
