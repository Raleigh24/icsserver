import logging
import os
import signal
import subprocess
import sys

import Pyro4 as Pyro

from ics import utils

logger = logging.getLogger(__name__)

python_bin = sys.executable

server_bin_map = {
    'icsserver': os.path.dirname(__file__) + '/icsserver.py',
    'icsalert_server': os.path.dirname(__file__) + '/icsalert_server.py'
}


class SubServerControl:
    """Control the processes that make up the ICS server."""

    @Pyro.expose
    def start(self):
        """Start server processes."""
        for server in server_bin_map.keys():
            # TODO: Check if server is already running
            server_bin = server_bin_map[server]
            cmd = [python_bin, server_bin]
            pid = subprocess.Popen(cmd).pid
            logger.info('ICS server started with PID ' + str(pid))
            pid_filename = utils.pid_filename(server)
            utils.create_pid_file(pid_filename, pid)

    @Pyro.expose
    def stop(self, force=False):
        """Stop server processes.

        Args:
            force (bool): Force the sub server to stop by using SIGTERM if necessary

        """
        for server in server_bin_map.keys():
            if utils.check_running(server):
                pid = int(utils.get_ics_pid(server))
                try:
                    os.kill(pid, signal.SIGKILL)
                except OSError as e:
                    logging.error('Unable to stop server ' + server)
                    if force:
                        logging.info('Force killing server ' + server)
                        os.kill(pid, signal.SIGTERM)
            else:
                logger.info('Found no server running')
