import logging
from datetime import datetime
try:
    import queue
except ImportError:
    import Queue as queue  # Python2 version

import mail
from environment import HOSTNAME, ICS_HOME, ICS_CLUSTER_NAME, ICS_ALERT_LOG
from ics_exceptions import ICSError

logger = logging.getLogger(__name__)
alert_queue = queue.Queue()

CRITICAL = 30
ERROR = 20
WARNING = 10
NOTSET = 0

_level_names = {
    CRITICAL: 'CRITICAL',
    ERROR: 'ERROR',
    WARNING: 'WARNING',
    NOTSET: 'NOTSET',
    'CRITICAL': CRITICAL,
    'ERROR': ERROR,
    'WARNING': WARNING,
    'NOTSET': NOTSET
}

alert_html_template_file = ICS_HOME + '/etc/alert.html'


def get_level_name(level):
    """Return the string representation of an alert level"""
    return _level_names[level]


class Alert:
    def __init__(self, resource, level, msg):
        self.time = datetime.now()
        self.time_fmt = self.time.strftime("%m/%d/%Y %H:%M:%S")
        self.system_name = ICS_CLUSTER_NAME
        self.host_name = HOSTNAME
        self.resource_name = resource.name
        self.group_name = resource.attr['Group']
        self.level = level
        self.levelname = get_level_name(level)
        self.msg = msg

    def __str__(self):
        return ' '.join([self.time_fmt, self.levelname, ICS_CLUSTER_NAME, self.group_name, self.resource_name, self.msg])

    def html(self):
        with open(alert_html_template_file, 'r') as FILE:
            alert_html_template = FILE.read()

        return alert_html_template.format(message=self.msg, system_name=ICS_CLUSTER_NAME, host_name=HOSTNAME,
                                          group_name=self.group_name, resource_name=self.resource_name,
                                          event_time=self.time_fmt)


def load_html_template(filename):
    with open(filename, 'r') as f:
        return f.read()


def render_template(alert, template):
    return template.format(message=alert.msg, system_name=ICS_CLUSTER_NAME, host_name=HOSTNAME,
                           group_name=alert.group_name, resource_name=alert.resource_name, event_time=alert.time_fmt)


def log_alert(alert):
    with open(ICS_ALERT_LOG, 'a+') as FILE:
        FILE.write(str(alert) + '\n')


# def mail_alert(alert, template):
#     for recipient in ALERT_RECIPIENTS:
#         sender = 'ics@' + HOSTNAME
#         subject = 'ICS {} Alert - {}'.format('Warning', alert.resource_name)
#         body = render_template(alert, template)
#         #try:
#         logger.debug('Sending alert to {}'.format(recipient))
#         mail.send_html(recipient, sender, subject, body)
#         #except Exception as e:
#         #logger.error('Unable to send mail: {}'.format(e))


def critical(resource, msg):
    alert = Alert(resource, CRITICAL, msg)
    alert_queue.put(alert)
    logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))


def error(resource, msg):
    alert = Alert(resource, ERROR, msg)
    alert_queue.put(alert)
    logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))


def warning(resource, msg):
    alert = Alert(resource, WARNING, msg)
    alert_queue.put(alert)
    logger.debug('Resource({}) Alert generated: {} '.format(resource.name, msg))


class AlertHandler:

    def __init__(self):
        self.daemon = True
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
        logging.info("Alert level changed from {} to {}".format(previous_level, get_level_name(self.alert_level)))

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
            queue_size = alert_queue.qsize()
            if queue_size > 0:
                logger.debug('Remaining events in alert queue ({})'.format(queue_size))
            alert = alert_queue.get()
            if alert.level >= self.alert_level:
                log_alert(alert)
                self.mail_alert(alert, self.html_template)
            del alert
