import os
import signal
import json
import logging
import sys
import subprocess

import Pyro4 as Pyro

from environment import ICS_VAR
from ics_exceptions import ICSError

logger = logging.getLogger(__name__)


def is_process_running(pid):
    """Determine if a process is running based on it's PID.

    Args:
        pid (str): PID of process.

    Returns:
        bool: True if running, false if not.

    """
    cmd = ['ps', '-p', pid]
    return_process = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    try:
        return_process.check_returncode()
    except subprocess.CalledProcessError:
        return False
    else:
        return True


def pid_filename(name):
    """Generate PID filename for a given server name.

    Args:
        name: Server name.

    Returns:
        str: Full path of PID file.

    """
    return ICS_VAR + '/{}.pid'.format(name)


def get_ics_pid(server):
    """Read ICS pid from pid file.

    Args:
        server (str): Name of server.

    Returns:
        str: PID of server stored in file.
    """
    with open(pid_filename(server), 'r') as f:
        pid = f.read()
    return pid


def check_running(server):
    """Determine if ICS server is running by attempting to read the PID file.

    Args:
        server (str): Name of server.

    Returns:
        bool: True if running, false if not.
    """
    if os.path.exists(pid_filename(server)):
        pid = get_ics_pid(server)
        return is_process_running(pid)
    else:
        return False


def create_pid_file(filename, pid):
    """Write new PID to PID file"""
    try:
        with open(filename, 'w') as f:
            f.write(str(pid))
    except IOError as e:
        print('ERROR: Unable to create PID file: {}'.format(e))


def cli_signal_handler(signal_code, frame):
    """Signal handler for command line interface commands"""
    if signal_code is signal.SIGINT:
        print('Exiting...')
        exit(1)
    else:
        print('ERROR: Received signal {}'.format(signal_code))
        print('Exiting...')
        exit(1)


def setup_signal_handler():
    """Setup signal handler for command line interface"""
    signal.signal(signal.SIGINT, cli_signal_handler)


def read_config(filename):
    """Read configuration file"""
    logger.info('Reading configuration file...')
    try:
        with open(filename, 'r') as f:
            data = json.load(f)
        return data
    except FileNotFoundError as error:
        logging.info('No configuration file found')
        raise
    except (ValueError, IOError) as error:
        logging.error('Error occurred while loading config: {}'.format(str(error)))
        return {}


def write_config(filename, data):
    """Write configuration to file"""
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)
    except IOError as error:
        logger.exception('Error occurred while writing file: {}'.format(str(error)))
        raise


def set_log_level(level):
    root_logger = logging.getLogger()
    level_map = {
        'CRITICAL': logging.CRITICAL,
        'ERROR': logging.ERROR,
        'WARNING': logging.WARNING,
        'INFO': logging.INFO,
        'DEBUG': logging.DEBUG,
        'NOTSET': logging.NOTSET
    }

    try:
        set_level = level_map[level]
        root_logger.setLevel(set_level)
    except KeyError:
        raise ICSError('Invalid logging level: {}'.format(level))

    logging.critical('Log level set: ' + level)



