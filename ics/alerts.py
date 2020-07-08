import logging
import socket
from datetime import datetime
from collections import namedtuple
try:
    import queue
except ImportError:
    import Queue as queue  # Python2 version

import Pyro4 as Pyro

import mail
from environment import HOSTNAME, ICS_HOME, ICS_CLUSTER_NAME, ICS_ALERT_LOG
from ics_exceptions import ICSError

logger = logging.getLogger(__name__)

CRITICAL = 40
ERROR = 30
WARNING = 20
INFO = 10
NOTSET = 0

_level_names = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    INFO: 'INFO',
    NOTSET: 'NOTSET',
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARNING': WARNING,
    'INFO': INFO,
    'NOTSET': NOTSET
}

Alert = namedtuple('Alert', 'resource group node time level msg')

alert_html_template_file = ICS_HOME + '/etc/alert.html'


def get_level_name(level):
    """Return the string representation of an alert level"""
    return _level_names[level]


def load_html_template(filename):
    with open(filename, 'r') as f:
        return f.read()


def render_template(alert, template):
    return template.format(message=alert.msg, system_name=ICS_CLUSTER_NAME, host_name=HOSTNAME,
                           group_name=alert.group, resource_name=alert.resource, event_time=alert.time)


def log_alert(alert):
    with open(ICS_ALERT_LOG, 'a+') as alert_log_file:
        alert_log = ' '.join([alert.time, alert.level, ICS_CLUSTER_NAME, alert.group, alert.resource, alert.msg])
        alert_log_file.write(alert_log + '\n')


def create_alert(resource, msg, level):
    now = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
    alert = Alert(
        resource=resource.name,
        group=resource.attr_value('Group'),
        node=HOSTNAME,
        time=now,
        level=level,
        msg=msg,
    )
    return alert


class AlertClient:
    """Alert interface for creating alerts."""

    def __init__(self):
        self.alert_server_uri = 'PYRO:alert_handler@' + socket.gethostname() + ':9092'
        self.alert_server = Pyro.Proxy(self.alert_server_uri)

    def critical(self, resource, msg):
        """Send alert with critical level.

        Args:
            resource (obj): Resource object.
            msg (str): Alert message.

        """
        logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))
        alert = create_alert(resource, msg, CRITICAL)
        self.alert_server.add_alert(alert)

    def error(self, resource, msg):
        """Send alert with error level.

        Args:
            resource (obj): Resource object.
            msg (str): Alert message.

        """
        logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))
        alert = create_alert(resource, msg, ERROR)
        self.alert_server.add_alert(alert)

    def warning(self, resource, msg):
        """Send alert with warning level.

        Args:
            resource (obj): Resource object
            msg (str): Alert message.

        """
        logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))
        alert = create_alert(resource, msg, WARNING)
        self.alert_server.add_alert(alert)


class AlertHandler:

    def __init__(self, cluster_name="", node_name=""):
        self.alert_queue = queue.Queue()
        self.alert_level = NOTSET
        self.recipients = []
        self.html_template = load_html_template(alert_html_template_file)

    def get_level(self):
        return get_level_name(self.alert_level)

    def set_level(self, level):
        previous_level = self.alert_level
        try:
            self.alert_level = get_level_name(level)
        except KeyError:
            raise ICSError('Invalid alert level')
        logger.info("Alert level changed from {} to {}".format(previous_level, get_level_name(self.alert_level)))

    def add_recipient(self, recipient):
        logger.info('Adding mail recipient {}'.format(recipient))
        self.recipients.append(recipient)

    def remove_recipient(self, recipient):
        logger.info('Removing mail recipient {}'.format(recipient))
        try:
            self.recipients.remove(recipient)
        except ValueError:
            raise ICSError('Recipient does not exist')

    def set_recipients(self, recipients):
        self.recipients = recipients

    @Pyro.expose
    def add_alert(self, alert):
        logger.info('Alert generated.............')
        # TODO format message
        self.alert_queue.put(alert)

    def mail_alert(self, alert, template):
        if not self.recipients:
            logger.warning('Alert recipient list is empty, no alerts sent')

        for recipient in self.recipients:
            sender = 'ics@' + HOSTNAME
            subject = 'ICS {} Alert - {}'.format('Warning', alert.resource_name)
            body = render_template(alert, template)
            logger.debug('Sending alert to {}'.format(recipient))
            try:
                mail.send_html(recipient, sender, subject, body)
            except Exception as e:
                logger.error('Unable to send mail: {}'.format(e))

    def run(self):
        while True:
            queue_size = self.alert_queue.qsize()
            if queue_size > 0:
                logger.debug('Remaining events in alert queue ({})'.format(queue_size))
            alert = self.alert_queue.get()
            if alert.level >= self.alert_level:
                log_alert(alert)
                self.mail_alert(alert, self.html_template)
            del alert
