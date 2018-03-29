import logging
from datetime import datetime

import config
import mail

logger = logging.getLogger(__name__)

alert_log_file = config.ICS_LOG + 'alerts.log'
alert_html_template = config.ICS_HOME + '/ics/alert.html'


class AlertSeverity:
    CRITICAL = 'critical'
    ERROR = 'error'
    WARNING = 'warning'
    INFO = 'info'



def send_alert(resource, severity, reason='', msg=''):

    resource_name = resource.name
    group_name = resource.attr['Group']
    system_name = config.CLUSTER_NAME
    event_time = str(datetime.now().strftime("%m/%d/%Y %H:%M:%S"))
    host_name = config.HOSTNAME

    with open(alert_log_file, 'a+') as FILE:
        log_str = ' '.join([event_time, severity, system_name, group_name, resource_name, reason])
        FILE.write(log_str + '\n')

    # Format html file with parameters
    with open(alert_html_template, 'r') as FILE:
        html = FILE.read()
    formatted_html = html.format(**locals())

    for recipient in config.ALERT_RECIPIENTS:
        from_addr = 'ics@' + config.HOSTNAME
        to_addr = recipient
        subject = 'ICS {} Alert - {}'.format('Warning', resource.name)
        try:
            mail.send_html(to_addr, from_addr, subject, formatted_html)
        except Exception as e:
            logger.error('Unable to send mail: {}'.format(e))
