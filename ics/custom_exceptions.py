class DoesNotExist(Exception):
    """Indicates an item does not exist"""
    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return self.msg


class AlreadyExists(Exception):
    """Indicates an item already exists"""
    def __init__(self, msg=''):
        self.msg = msg

    def __str__(self):
        return self.msg


class TimeoutExpired(Exception):
    """This exception is raised when the timeout expires while waiting for a child process"""
    pass


class ResourceAttributeError(Exception):
    pass


class NetworkConnectionError(Exception):
    pass