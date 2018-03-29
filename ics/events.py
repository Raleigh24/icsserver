import logging
try:
    import queue
except ImportError:
    import Queue as queue  # Python2 version

from states import ResourceStates, ONLINE_STATES, OFFLINE_STATES
from alerts import AlertSeverity, send_alert

logger = logging.getLogger(__name__)

event_queue = queue.Queue()


def trigger_event(event):
    """Add event to event queue"""
    logger.debug('Resource({}) event triggered {}'.format(event.resource.name, event))
    event_queue.put(event)


def event_handler():
    """Continuously execute events in event queue"""
    while True:
        queue_size = event_queue.qsize()
        if queue_size > 0:
            logger.debug('Remaining events in event queue ({})'.format(queue_size))
        event = event_queue.get()
        logger.debug('Running event ({})'.format(event))
        event.run()
        del event


class Event:
    """Base event class"""
    def run(self):
        pass


class PollEvent(Event):
    """Base poll event class"""
    def __init__(self, resource):
        self.resource = resource

    def __str__(self):
        return '{} for {}'.format(self.__class__.__name__, self.resource.name)

    def run(self):
        pass


class PollRunEvent(PollEvent):
    def run(self):
        self.resource.poll()


class PollOnlineEvent(PollEvent):
    def run(self):
        if self.resource.state is not ResourceStates.FAULTED:
            self.resource.change_state(ResourceStates.ONLINE)


class PollOfflineEvent(PollEvent):
    def run(self):
        if self.resource.state is not ResourceStates.FAULTED:
            self.resource.change_state(ResourceStates.OFFLINE)


class PollUnknownEvent(PollEvent):
    def run(self):
        self.resource.change_state(ResourceStates.UNKNOWN)


class ResourceStateEvent(Event):
    """Base resource event class"""
    def __init__(self, resource, last_state):
        self.resource = resource
        self.last_state = last_state

    def __str__(self):
        return '{} for {}'.format(self.__class__.__name__, self.resource.name)

    def run(self):
        pass


class ResourceOfflineEvent(ResourceStateEvent):
    def run(self):
        if self.last_state in ONLINE_STATES:
            self.resource.fault_count += 1
            logger.info('Resource({}) fault detected'.format(self.resource.name))
            logger.debug('Resource({}) last state: {}'.format(self.resource.name, self.last_state))

            if self.resource.fault_count >= self.resource.attr['RestartLimit']:
                logger.info('Resource({}) reached max fault count ({})'
                             .format(self.resource.name, self.resource.attr['RestartLimit']))
                self.resource.change_state(ResourceStates.FAULTED)
            elif self.resource.attr['AutoRestart'] == 'true':
                self.resource.change_state(ResourceStates.STARTING)
        elif self.resource.propagate:
            self.resource.propagate = False  # Resource has successfully propagated from parent
            for parent in self.resource.parents:
                if parent.children_ready():
                    logger.info('Resource({}) propagating offline to {} '.format(self.resource.name, parent.name))
                    parent.propagate = True
                    if parent.state is ResourceStates.ONLINE:
                        parent.change_state(ResourceStates.STOPPING)
                    elif parent.state is ResourceStates.OFFLINE:
                        parent.change_state(ResourceStates.OFFLINE, force=True)  # Needed to continue propagation
                else:
                    logger.debug('Resource({}) Unable to stop, waiting for children to become offline'
                                 .format(parent.name))


class ResourceStoppingEvent(ResourceStateEvent):
    def run(self):
        self.resource.stop()


class ResourceOnlineEvent(ResourceStateEvent):
    def run(self):
        if self.last_state in OFFLINE_STATES:
            logger.warning('Resource({}) came online unexpectedly'.format(self.resource.name))
            send_alert(self.resource, AlertSeverity.WARNING, reason='Resource came online by itself')
        elif self.resource.propagate:
            self.resource.propagate = False  # Resource has successfully propagated from children
            for child in self.resource.children:
                if child.parents_ready():
                    logger.info('Resource({}) propagating online to {} '.format(self.resource.name, child.name))
                    child.propagate = True
                    if child.state in ResourceStates.OFFLINE:
                        child.change_state(ResourceStates.STARTING)
                    elif child.state is ResourceStates.ONLINE:
                        child.change_state(ResourceStates.ONLINE, force=True)  # Needed to continue propagation
                else:
                    logger.debug('Resource({}) Unable to start, waiting for parents to become online'
                                  .format(child.name))


class ResourceStartingEvent(ResourceStateEvent):
    def run(self):
        self.resource.start()


class ResourceFaultedEvent(ResourceStateEvent):
    def run(self):
        self.resource.flush()
        trigger_event(AlertEvent(self.resource))
        send_alert(self.resource, AlertSeverity.ERROR, reason='Resource faulted')
        # TODO: propagate any offline


class ResourceUnknownEvent(ResourceStateEvent):
    def run(self):
        if self.last_state is not ResourceStates.UNKNOWN:
            send_alert(self.resource, AlertSeverity.WARNING, reason='Resource in unknown state')


class AlertEvent(Event):
    def __init__(self, resource, severity=''):
        self.resource = resource
        self.resource_name = self.resource.name
        self.group_name = 'test'
        self.severity = severity

    def run(self):
        pass
        #send_alert(self.resource_name, self.group_name, self.severity)








