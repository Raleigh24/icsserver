#!/usr/bin/env bash

export ICS_HOME=${ICS_HOME:-/opt/ICS}
source ${ICS_HOME}/test/test_setup.sh

group_name=group-a
echo "Creating group ${group_name}"
${ICSGRP} -add ${group_name}

resource_name="proc-a1"
echo "Creating resource ${resource_name}"
${ICSRES} -add ${resource_name} ${group_name}
${ICSRES} -modify ${resource_name} StartProgram "${RES_SCRIPT} start ${resource_name}"
${ICSRES} -modify ${resource_name} StopProgram "${RES_SCRIPT} stop ${resource_name}"
${ICSRES} -modify ${resource_name} MonitorProgram "${RES_SCRIPT}  monitor ${resource_name}"
${ICSRES} -modify ${resource_name} MonitorInterval 5
${ICSRES} -modify ${resource_name} OfflineMonitorInterval 5

echo "Enabling group"
${ICSGRP} -enableresources ${group_name}
${ICSGRP} -enable ${group_name}
