import os

ICS_VERSION = '1.3.0'

# Default environment settings
DEFAULT_ICS_HOME = '/opt/ICS'
DEFAULT_ICS_LOG = '/var/opt/ics/log'
DEFAULT_ICS_CONF = '/var/opt/ics/config'
DEFAULT_ICS_VAR = '/var/opt/ics'
DEFAULT_ICS_UDS = '/var/opt/ics/uds'

# Global configuration variables
HOSTNAME = os.uname()[1]
ICS_HOME = os.getenv('ICS_HOME', DEFAULT_ICS_HOME)
ICS_LOG = os.getenv('ICS_LOG', DEFAULT_ICS_LOG)
ICS_CONF = os.getenv('ICS_CONF', DEFAULT_ICS_CONF)
ICS_VAR = os.getenv('ICS_VAR', DEFAULT_ICS_VAR)
ICS_UDS = os.getenv('ICS_UDS', DEFAULT_ICS_UDS)

ICS_CONF_FILE = ICS_CONF + '/main.cf'
ICS_UDS_FILE = ICS_UDS + '/uds_socket'
ICS_ALERT_LOG = ICS_LOG + '/alerts.log'
ICS_RES_LOG = ICS_LOG + '/resource.log'

ICS_CLUSTER_NAME = HOSTNAME  # Temporary
ICS_ALERT_RECIPIENTS = ["raleigh.waters@intelsat.com"]
ICS_ALERT_LEVEL = 'NOTSET'
