import argparse
import subprocess
import sys

import config
import utilities


def start_server():
    """Start server by creating new process"""
    python_bin = sys.executable
    cmd = [python_bin, config.ICS_HOME + '/ics/icsserver.py']
    pid = subprocess.Popen(cmd).pid
    utilities.create_pid_file(pid)


if __name__ == '__main__':
    utilities.setup_signal_handler()
    description_text = 'Start ICS server'
    epilog_text = ''
    parser = argparse.ArgumentParser(description=description_text)
    parser.add_argument('-v', '--version', action='store_true', help='')
    args = parser.parse_args()

    if args.version is True:
        print('Version: ' + config.ICS_VERSION)
    else:
        if utilities.check_running():
            print('ERROR: Server is already running')
            exit(1)
        else:
            start_server()












