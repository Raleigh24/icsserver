import argparse
import os
import signal

import utilities


def stop_server():
    pass


if __name__ == '__main__':
    utilities.setup_signal_handler()
    description_text = 'Stop ICS server'
    epilog_text = ''
    parser = argparse.ArgumentParser(description=description_text)
    parser.add_argument('-force', action='store_true', help="")
    args = parser.parse_args()

    if utilities.check_running():
        pid = int(utilities.get_ics_pid())
    else:
        print('ERROR: Found no server running')
        exit(1)

    if args.force is True:
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError as e:
            print('ERROR: Unable to stop server')
            print('Reason: {}'.format(e))
            exit(1)
    else:
        try:
            os.kill(pid, signal.SIGTERM)
        except OSError as e:
            print('ERROR: Unable to stop server')
            print('Reason: {}'.format(e))
        stop_server()






