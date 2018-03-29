import os

import config


def is_process_running(pid):
    """Determine if a process is running based on it's PID"""
    return os.path.exists('/proc/' + str(pid))


def get_ics_pid():
    """Read ICS pid from pid file"""
    with open(config.PID_FILE, 'r') as f:
        pid = f.read()
    return pid


def check_running():
    """Determine if ICS server is running by attempting to read the PID file"""
    if os.path.exists(config.PID_FILE):
        pid = get_ics_pid()
        return is_process_running(pid)
    else:
        False


def create_pid_file(pid):
    """Write new PID to PID file"""
    try:
        with open(config.PID_FILE, 'w') as f:
            f.write(str(pid))
    except IOError as e:
        print 'ERROR: Unable to create PID file: {}'.format(e)
