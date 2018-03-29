import json
import os
import logging.config


ICS_HOME = os.getenv('ICS_HOME')
if ICS_HOME is None:
    print 'ERROR environment variable ICS_HOME is not set. Exiting...'
    exit(1)

# Read ICS configuration file
icsConfigFile = ICS_HOME + '/etc/ics.conf'
with open(icsConfigFile) as FILE:
    jsonData = json.load(FILE)

# Global configuration variables
HOSTNAME = os.uname()[1]
ICS_LOG = os.getenv('ICS_LOG', jsonData['locations']['ICS_LOG'])
ICS_CONF = os.getenv('ICS_CONF', jsonData['locations']['ICS_CONF'])
RES_CONF = os.getenv('RES_CONF', jsonData['locations']['RES_CONF'])
ICS_PORT = os.getenv('ICS_PORT', jsonData['network']['listening_port'])
CLUSTER_NAME = jsonData['cluster']['cluster_name']
ALERT_RECIPIENTS = jsonData['notifications']['recipients']
ICS_VERSION = jsonData['version']['number']
ICS_VAR = jsonData['locations']['ICS_VAR']
PID_FILE = ICS_VAR + '/icsserver.pid'


def create_logger():
    if not os.path.isdir(ICS_LOG):
        try:
            os.makedirs(ICS_LOG)
        except OSError as e:
            print 'ERROR: Unable to create log directory: {}'.format(e)
            print 'Exiting...'
            exit(1)
    # TODO: Check if file path exists
    logging.logFilename = ICS_LOG + '/icsserver.log'
    try:
        logging.config.fileConfig(ICS_HOME + '/ics/logging.conf')
    except IOError as e:
        print 'ERROR: Unable to create log file: {}'.format(e)
        exit(1)

