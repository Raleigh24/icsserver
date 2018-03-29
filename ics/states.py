class ResourceStates:
    OFFLINE = 'offline'  # 0
    STARTING = 'starting'  # 1
    ONLINE = 'online'  # 2
    STOPPING = 'stopping'  # 3
    FAULTED = 'faulted'  # 4
    UNKNOWN = 'unknown'  # 5


ONLINE_STATES = (
    ResourceStates.STARTING,
    ResourceStates.ONLINE
)

OFFLINE_STATES = (
    ResourceStates.OFFLINE,
    ResourceStates.STOPPING,
    ResourceStates.FAULTED,
    ResourceStates.UNKNOWN
)

TRANSITION_STATES = (
    ResourceStates.STARTING,
    ResourceStates.STOPPING
)


class GroupStates:
    ONLINE = 'online'
    PARTIAL = 'partial'
    OFFLINE = 'offline'
    FAULTED = 'faulted'
    UNKNOWN = 'unknown'
