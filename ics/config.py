import json
import os
import logging.config

from environment import ICS_HOME
from environment import ICS_LOG


def create_logger():
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

