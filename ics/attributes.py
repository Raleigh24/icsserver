resourceAttributes = {
    "resource": {
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
            "default": "55",
            "type": "int",
            "description": ""
        },
        "OfflineMonitorInterval": {
            "default": "55",
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
        "AutoRestart": {
            "default": "true",
            "type": "boolean",
            "description": ""
        },
        "AutoStart": {
            "default": "true",
            "type": "boolean",
            "description": ""
        }
    }
}


group_attributes = {
    "Enabled": {
        "default": "false",
        "type": "boolean",
        "description": ""
    }
}


system_attributes = {
    "ResourceLimit": {
        "default": "5000",
        "type": "int",
        "description": "Maximum number of resources"
    }
}