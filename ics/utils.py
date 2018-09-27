import os
import signal
import json

from environment import ICS_PID_FILE


def is_process_running(pid):
    """Determine if a process is running based on it's PID"""
    return os.path.exists('/proc/' + str(pid))


def get_ics_pid():
    """Read ICS pid from pid file"""
    with open(ICS_PID_FILE, 'r') as f:
        pid = f.read()
    return pid


def check_running():
    """Determine if ICS server is running by attempting to read the PID file"""
    if os.path.exists(ICS_PID_FILE):
        pid = get_ics_pid()
        return is_process_running(pid)
    else:
        False


def create_pid_file(pid):
    """Write new PID to PID file"""
    try:
        with open(ICS_PID_FILE, 'w') as f:
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


def read_json(filename):
    """Read data from configuration file and return data"""
    try:
        with open(filename, 'r') as file:
            return json.load(file)
    except IOError as error:
        #logger.error('Unable to load config file {}, {}'.format(filename, str(error)))
        raise


def write_json(filename, data):
    """Write configuration data in json to file"""
    try:
        with open(filename, 'w') as file:
            json.dump(data, file, indent=4, sort_keys=True)
    except IOError as error:
        #logger.error('Unable to save config file {}, {}'.format(filename, str(error)))
        raise

#def set_log_level(level):

