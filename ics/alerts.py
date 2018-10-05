import logging
from datetime import datetime

import mail
from environment import HOSTNAME, ICS_HOME, ICS_CLUSTER_NAME, ICS_ALERT_LOG, ICS_ALERT_RECIPIENTS

logger = logging.getLogger(__name__)

alert_html_template = ICS_HOME + '/etc/alert.html'


class AlertSeverity:
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'


def send_alert(resource, severity, reason='', msg=''):

    resource_name = resource.name
    group_name = resource.attr['Group']
    system_name = ICS_CLUSTER_NAME
    event_time = str(datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    host_name = HOSTNAME

    with open(ICS_ALERT_LOG, 'a+') as FILE:
        log_str = ' '.join([event_time, severity, system_name, group_name, resource_name, reason])
        FILE.write(log_str + '\n')

    # Format html file with parameters
    with open(alert_html_template, 'r') as FILE:
        html = FILE.read()
    formatted_html = html.format(**locals())

    for recipient in ICS_ALERT_RECIPIENTS:
        from_addr = 'ics@' + HOSTNAME
        to_addr = recipient
        subject = 'ICS {} Alert - {}'.format('Warning', resource.name)
        try:
            mail.send_html(to_addr, from_addr, subject, formatted_html)
        except Exception as e:
            logger.error('Unable to send mail: {}'.format(e))
