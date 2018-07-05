import argparse
import subprocess
import sys

import config
import utils
from environment import ICS_HOME
from environment import ICS_VERSION



def start_server():
    """Start server by creating new process"""
    python_bin = sys.executable
    cmd = [python_bin, ICS_HOME + '/ics/icsserver.py']
    pid = subprocess.Popen(cmd).pid
    utils.create_pid_file(pid)


if __name__ == '__main__':
    utils.setup_signal_handler()
    description_text = 'Start ICS server'
    epilog_text = ''
    parser = argparse.ArgumentParser(description=description_text)
    parser.add_argument('-v', '--version', action='store_true', help='')
    args = parser.parse_args()

    if args.version is True:
        print('Version: ' + ICS_VERSION)
    else:
        if utils.check_running():
            print('ERROR: Server is already running')
            exit(1)
        else:
            start_server()












