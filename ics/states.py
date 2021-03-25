class ResourceStates:
    OFFLINE = 'offline'  # 0
    STARTING = 'starting'  # 1
    ONLINE = 'online'  # 2
    STOPPING = 'stopping'  # 3
    FAULTED = 'faulted'  # 4
    UNKNOWN = 'unknown'  # 5


class GroupStates:
    ONLINE = 'online'
    PARTIAL = 'partial'
    OFFLINE = 'offline'
    FAULTED = 'faulted'
    UNKNOWN = 'unknown'


class NodeStates:
    ONLINE = 'online'
    OFFLINE = 'offline'
    CRITICAL = 'critical'


ONLINE_STATES = (
    ResourceStates.STARTING,
    ResourceStates.ONLINE,
    GroupStates.ONLINE,
    GroupStates.PARTIAL
)

OFFLINE_STATES = (
    ResourceStates.OFFLINE,
    ResourceStates.STOPPING,
    ResourceStates.FAULTED,
    ResourceStates.UNKNOWN,
    GroupStates.OFFLINE,
    GroupStates.FAULTED,
    GroupStates.UNKNOWN
)

TRANSITION_STATES = (
    ResourceStates.STARTING,
    ResourceStates.STOPPING
)
