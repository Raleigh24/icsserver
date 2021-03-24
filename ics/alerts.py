import logging
import os
import socket
from datetime import datetime

try:
    import queue
except ImportError:
    import Queue as queue  # Python2 version

import Pyro4 as Pyro

from ics import mail
from ics.environment import HOSTNAME, ICS_CLUSTER_NAME, ICS_ALERT_PORT
from ics.errors import ICSError
from ics.utils import alert_log_name
from ics.utils import engine_conn

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

alert_html_template_file = os.path.dirname(__file__) + '/templates/alert.html'


def get_level_name(level):
    """Return the string representation of an alert level.

    Args:
        level: Alert level

    Returns:
        Alert level name.

    """
    return _level_names[level]


def load_html_template(filename):
    """Load HTML template from file.

    Args:
        filename (str): HTML template filename.

    Returns:
        str: HTML template.

    """
    with open(filename, 'r') as f:
        return f.read()


def log_alert(alert):
    """Log alert using alert object.

    Args:
        alert (obj): Alert object.

    """
    with open(alert_log_name(), 'a+') as alert_log_file:
        alert_log_file.write(str(alert) + '\n')


def create_alert(resource, msg, level):
    """Create alert object from resource object.

    Args:
        resource (obj): Resource object.
        msg (str): Alert message.
        level (int): Alert level number.

    Returns:
        obj: Alert named tuple.

    """
    return Alert(resource.name, resource.attr_value('Group'), level, msg)


def create_test_alert(msg, level):
    """Create alert object for testing.

    Args:
        msg (str): Alert message.
        level (int): Alert level number.

    Returns:
        obj: Alert named tuple.

    """
    return Alert('Test_Resource', 'Test_Group', level, msg)


class Alert:
    """Alert object."""

    def __init__(self, resource, group, level, msg, node=HOSTNAME, time=None):
        self.resource = resource
        self.group = group
        self.node = node
        self.level = level
        self.msg = msg
        if time is None:
            self.time = datetime.now().strftime("%m/%d/%Y %H:%M:%S")
        else:
            self.time = time

    def __str__(self):
        return ' '.join([self.time, get_level_name(self.level), ICS_CLUSTER_NAME, self.group, self.resource,
                         '\"' + self.msg + '\"'])

    def html(self, template):
        """Render alert as HTML.

        Args:
            template (str): HTML alert template.

        Returns:
            str: HTML to used to represent an alert.

        """
        return template.format(message=self.msg, system_name=ICS_CLUSTER_NAME, host_name=HOSTNAME,
                               group_name=self.group, resource_name=self.resource, event_time=self.time)

    def asdict(self):
        """Alert information in dict format. Mainly used to send alert over serialization.

        Returns:
            dict: Alert as a dict.

        """
        return {
            'resource': self.resource,
            'group': self.group,
            'node': self.node,
            'time': self.time,
            'level': self.level,
            'msg': self.msg
        }


class AlertClient:
    """Alert interface for creating alerts."""

    def __init__(self):
        self.alert_server_uri = 'PYRO:alert_handler@' + socket.gethostname() + ':' + str(ICS_ALERT_PORT)
        self.alert_server = Pyro.Proxy(self.alert_server_uri)

    def critical(self, resource, msg):
        """Send alert with critical level.

        Args:
            resource (obj): Resource object.
            msg (str): Alert message.

        """
        logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))
        alert = create_alert(resource, msg, CRITICAL)
        self.send_alert(alert)

    def error(self, resource, msg):
        """Send alert with error level.

        Args:
            resource (obj): Resource object.
            msg (str): Alert message.

        """
        logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))
        alert = create_alert(resource, msg, ERROR)
        self.send_alert(alert)

    def warning(self, resource, msg):
        """Send alert with warning level.

        Args:
            resource (obj): Resource object
            msg (str): Alert message.

        """
        logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))
        alert = create_alert(resource, msg, WARNING)
        self.send_alert(alert)

    def test(self, msg):
        """Send test alert message.

        Args:
            msg (str): Alert message.

        """
        logger.debug('Test alert generated: {} '.format(msg))
        alert = create_test_alert(msg, WARNING)
        self.send_alert(alert)

    def send_alert(self, alert):
        """Send alert to ICS alert server.

            Note: The alert must be sent as a dict, due to pyro not being able to send a serialized custom class.

        Args:
            alert (obj): Alert object.

        """
        self.alert_server.add_alert(alert.asdict())


class AlertHandler:
    """Handle alerts in queue."""

    def __init__(self, cluster_name="", node_name=""):
        self.alert_queue = queue.Queue()
        self.alert_level = NOTSET
        self.html_template = load_html_template(alert_html_template_file)

    def get_level(self):
        """Get alert level threshold of handler.

        Returns:
            int: Alert level.

        """
        return get_level_name(self.alert_level)

    def set_level(self, level):
        """Set alert level threshold of handler.

        Args:
            level (int): Alert Level.

        Raises:
            ICSError: When invalid alert level given.

        """
        previous_level = self.alert_level
        try:
            self.alert_level = get_level_name(level)
        except KeyError:
            raise ICSError('Invalid alert level')
        logger.info("Alert level changed from {} to {}".format(previous_level, get_level_name(self.alert_level)))

    def recipients(self):
        cluster = engine_conn()
        try:
            email_addressses = cluster.node_value('AlertRecipients')
        except Pyro.errors.CommunicationError:
            logger.error("Unable to connect to ICS engine to retrieve alert recipients")
            email_addressses = []

        return email_addressses

    @Pyro.expose
    def add_alert(self, alert_dict):
        """Add alert to alert handler queue.

        Args:
            alert_dict(dict): Alert in dict format.

        """
        alert = Alert(alert_dict['resource'], alert_dict['group'], alert_dict['level'], alert_dict['msg'],
                      node=alert_dict['node'], time=alert_dict['time'])

        logger.info('Alert generated ' + str(alert))
        self.alert_queue.put(alert)

    def mail_alert(self, alert, template):
        """Mail alert.

        Args:
            alert (obj): Alert object.
            template (str): HTML template.

        """
        if not self.recipients:
            logger.warning('Alert recipient list is empty, no alerts sent')

        for recipient in self.recipients():
            logger.info('Sending alert to {}'.format(recipient))
            sender = 'ics@' + HOSTNAME
            subject = 'ICS {} Alert - {}'.format('Warning', alert.resource)
            body = alert.html(template)
            try:
                mail.send_html(recipient, sender, subject, body)
            except ConnectionRefusedError as err:
                logger.error('Unable to send mail: {}'.format(err))
            except Exception as err:
                logger.exception('Unknown exception occurred: ' + str(err))

    def run(self):
        """Continuously read and execute alerts from alert queue."""
        while True:
            alert = self.alert_queue.get()  # Blocking until new alert available.
            if alert.level >= self.alert_level:
                log_alert(alert)
                try:
                    self.mail_alert(alert, self.html_template)
                except Exception as err:
                    logger.exception("Unknown exception occurred: " + str(err))
                    continue
            del alert
            queue_size = self.alert_queue.qsize()
            if queue_size > 0:
                logger.debug('Remaining events in alert queue ({})'.format(queue_size))
