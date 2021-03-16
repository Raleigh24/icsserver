import logging
from copy import deepcopy

from ics.errors import ICSError

logger = logging.getLogger(__name__)


class AttributeObject(object):  # Inherits from object to enabling super() in python2.7
    """Base class for for objects with attributes.

    Class Attributes:
        update_flag (bool): Global flag that shows when a attribute has changed for any instance.

    Attributes:
        name (str): Object name.
        default_attr (dict): Dictionary of default attribute values.

    """

    update_flag = False

    def __init__(self):
        self.name = None
        self._attr = {}
        self.default_attr = None

    def init_attr(self, default_attributes):
        """Initialize attributes with defaults.

        Args:
            default_attributes (dict): Dictionary of default attributes and values.

        """
        self.default_attr = default_attributes
        for attribute in default_attributes:
            default_value = default_attributes[attribute]['default']
            if isinstance(default_value, list):
                # Perform deep copy as to not reference the default instance
                self._attr[attribute] = deepcopy(default_value)
            else:
                self._attr[attribute] = default_value

    def modified_attributes(self):
        """Return dictionary of modified attributes (non-default).

        Returns:
            dict: attribute values that have changed from their default values.

        """
        # TODO: ChainMap in python 3
        data = {}
        for attribute in self._attr:
            attribute_value = self._attr[attribute]
            if attribute_value != self.default_attr[attribute]['default']:
                data[attribute] = attribute_value
        return data

    def attr_type(self, attr):
        """Return attribute type for a given attribute.

        Args:
            attr (str): Attribute name.

        Returns:
            str: Attribute type.

        """
        return self.default_attr[attr]['type']

    def set_attr(self, attr, value):
        """Set attribute value.

        Args:
            attr (str): Attribute name.
            value (str): Value to set attribute.

        Raises:
            ICSError: When given attribute does not exist.

        """
        if attr not in self._attr:
            raise ICSError('{}({}) Attribute {} does not exist'.format(self.__class__.__name__, self.name, attr))

        if self.attr_type(attr) == 'list':
            if not isinstance(value, list):
                raise ICSError('{}({}) Value {} is not of list type for attribute {}'.format(self.__class__.__name__, self.name, value, attr))

        if self._attr[attr] == "":
            previous_value = '<empty>'
        else:
            previous_value = self._attr[attr]
        self._attr[attr] = value
        AttributeObject.update_flag = True
        logger.info('{}({}) attribute {} changed from {} to {}'.format(self.__class__.__name__, self.name, attr,
                                                                       previous_value, value))

    def attr_append_value(self, attr, value):
        """Append item to list type attribute.

        Args:
            attr (str): Attribute value name.
            value (str): Value to set attribute

        Raises:
            ICSError: When given attribute is not valid or of list type.

        """
        logger.info('{}({}) Appending {} to attribute {}'.format(self.__class__.__name__, self.name, value, attr))
        if attr not in self._attr:
            raise ICSError('{}({}) Attribute {} does not exist'.format(self.__class__.__name__, self.name, attr))

        if self.default_attr[attr]['type'] != 'list':
            raise ICSError(('{}({}) Attribute {} is not of type \'list\''.format(self.__class__.__name__,
                                                                                 self.name, attr)))
        if value in self.attr_value(attr):
            raise ICSError('{}({}) Value {} already exists in attribute {}'.format(self.__class__.__name__,
                                                                                   self.name, value, attr))

        self._attr[attr].append(value)
        AttributeObject.update_flag = True

    def attr_remove_value(self, attr, value):
        """Remove item from list type attribute.

        Args:
            attr (str): Attribute value name.
            value (str): Value to set attribute

        Raises:
            ICSError: When given attribute is not valid or of list type.

        """
        logger.info('{}({}) Removing {} from attribute {}'.format(self.__class__.__name__, self.name, value, attr))
        if attr not in self._attr:
            raise ICSError('{}({}) Attribute {} does not exist'.format(self.__class__.__name__, self.name, attr))

        if self.default_attr[attr]['type'] != 'list':
            raise ICSError(('{}({}) Attribute {} is not of type \'list\''.format(self.__class__.__name__,
                                                                                 self.name, attr)))
        try:
            self._attr[attr].remove(value)
        except ValueError:
            raise ICSError(('{}({}) Value {} is not in attribute list {}'.format(self.__class__.__name__, self.name,
                                                                                 value, attr)))
        AttributeObject.update_flag = True

    def attr_value(self, attr):
        """Retrieve value of attribute.

        Args:
            attr (str): Attribute value name.

        Returns:
            obj: Attribute value.

        Raises:
            ICS_Error: When given attribute doesn't exist.

        """
        if attr not in self._attr:
            raise ICSError('{}({}) Attribute {} does not exist'.format(self.__class__.__name__, self.name, attr))
        else:
            return self._attr[attr]

    def attr_list(self):
        """Return a list of attributes and their values.

        Returns:
            list: List of attribute name, value tuples

        """
        attr_list = []
        for attr in self._attr:
            attr_list.append((attr, self._attr[attr]))
        return attr_list


resource_attributes = {
    "Group": {
        "default": "none",
        "type": "string",
        "description": ""
    },
    "Enabled": {
        "default": "false",
        "type": "boolean",
        "description": ""
    },
    "StartProgram": {
        "default": "",
        "type": "string",
        "description": ""
    },
    "StopProgram": {
        "default": "",
        "type": "string",
        "description": ""
    },
    "MonitorProgram": {
        "default": "",
        "type": "string",
        "description": ""
    },
    "FaultPropagation": {
        "default": "false",
        "type": "boolean",
        "description": ""
    },
    "OnlineRetryLimit": {
        "default": "0",
        "type": "int",
        "description": ""
    },
    "RestartLimit": {
        "default": 3,
        "type": "int",
        "description": "Number of times to retry bringing the resource online when\
                       it is taken offline unexpectedly before declaring it faulted"
    },
    "MonitorOnly": {
        "default": "false",
        "type": "boolean",
        "description": ""
    },
    "MonitorInterval": {
        "default": "60",
        "type": "int",
        "description": ""
    },
    "OfflineMonitorInterval": {
        "default": "180",
        "type": "int",
        "description": ""
    },
    "OnlineTimeout": {
        "default": "60",
        "type": "int",
        "description": "Maximum time (in seconds) within which the online\
                        function must complete or else be terminated"
    },
    "OfflineTimeout": {
        "default": "60",
        "type": "int",
        "description": "Maximum time (in seconds) within which the offline\
                        function must complete or else be terminated"
    },
    "MonitorTimeout": {
        "default": "60",
        "type": "int",
        "description": "Maximum time (in seconds) within which the monitor\
                        function must complete or else be terminated"
    },
    "Load": {
        "default": "1",
        "type": "integer",
        "description": ""
    }
}

group_attributes = {
    "SystemList": {
        "default": [],
        "type": "list",
        "description": "",
    },
    "Enabled": {
        "default": "false",
        "type": "boolean",
        "description": ""
    },
    "AutoStart": {
        "default": "false",
        "type": "boolean",
        "description": "Indicates weather a service group is automatically started when system starts"
    },
    "IgnoreDisabled": {
        "default": "false",
        "type": "boolean",
        "description": ""
    },
    "Parallel": {
        "default": "false",
        "type": "boolean",
        "description": ""
    }

}

system_attributes = {
    "ClusterName": {
        "default": "",
        "type": "string",
        "description": "The name of the cluster"
    },
    # "NodeName": {
    #     "default": "",
    #     "type": "string",
    #     "description": "The name of the node"
    # },
    "NodeList": {
        "default": [],
        "type": "list",
        "description": ""
    },
    "GroupLimit": {
        "default": "200",
        "type": "int",
        "description": ""
    },
    "ResourceLimit": {
        "default": "5000",
        "type": "int",
        "description": "Maximum number of resources"
    },
    "BackupInterval": {
        "default": "1",
        "type": "int",
        "description": ""
    },
    "AlertRecipients": {
        "default": [],
        "type": "list",
        "description": ""
    },
    "AlertLevel": {
        "default": "WARNING",
        "type": "string"
        "description"
    }
}
