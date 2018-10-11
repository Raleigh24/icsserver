import logging
from datetime import datetime
try:
    import queue
except ImportError:
    import Queue as queue  # Python2 version

import mail
from environment import HOSTNAME, ICS_HOME, ICS_CLUSTER_NAME, ICS_ALERT_LOG, ICS_ALERT_RECIPIENTS, ICS_ALERT_LEVEL

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


def set_level(level):
    global ICS_ALERT_LEVEL
    previous_level = ICS_ALERT_LEVEL
    ICS_ALERT_LEVEL = get_level_name(level)
    logging.info("Alert level changed from {} to {}".format(previous_level, get_level_name(ICS_ALERT_LEVEL)))


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


def mail_alert(alert, template):
    for recipient in ICS_ALERT_RECIPIENTS:
        from_addr = 'ics@' + HOSTNAME
        to_addr = recipient
        subject = 'ICS {} Alert - {}'.format('Warning', alert.resource_name)
        body = render_template(alert, template)
        try:
            mail.send_html(to_addr, from_addr, subject, body)
        except Exception as e:
            logger.error('Unable to send mail: {}'.format(e))


def critical(resource, msg):
    alert = Alert(resource, CRITICAL, msg)
    alert_queue.put(alert)


def error(resource, msg):
    alert = Alert(resource, ERROR, msg)
    alert_queue.put(alert)


def warning(resource, msg):
    alert = Alert(resource, WARNING, msg)
    alert_queue.put(alert)


def alert_handler():
    alert_html_template = load_html_template(alert_html_template_file)

    while True:
        queue_size = alert_queue.qsize()
        if queue_size > 0:
            logger.debug('Remaining events in alert queue ({})'.format(queue_size))
        alert = alert_queue.get()
        if alert.level >= ICS_ALERT_LEVEL:
            log_alert(alert)
            mail_alert(alert, alert_html_template)
        del alert
