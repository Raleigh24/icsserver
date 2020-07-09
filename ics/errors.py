"""
Definition of ICS exceptions and exception utilites
"""

from Pyro4.util import SerializerBase


class ICSError(Exception):
    """General exception indicating an error occurred performing an ICS action"""
    pass


def exception_convert(classname, serialized):
    obj = ICSError(*serialized['args'])
    obj._pyroTraceback = serialized["attributes"]["_pyroTraceback"]
    return obj


SerializerBase.register_dict_to_class("ics.errors.ICSError", exception_convert)
