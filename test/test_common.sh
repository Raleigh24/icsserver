#!/usr/bin/env bash

export ICS_HOME=/opt/ICS

################################################################################
# Global Variables
################################################################################
ICSSTART=${ICS_HOME}/bin/icsstart
ICSSTOP=${ICS_HOME}/bin/icsstop
ICSRES=${ICS_HOME}/bin/icsres
ICSGRP=${ICS_HOME}/bin/icsgrp
ICSSYS=${ICS_HOME}/bin/icssys

ICS_VAR=/var/opt/ics
ICS_CONFIG=${ICS_VAR}/config/main.cf

RES_FILES=${ICS_VAR}/test_resources
RES_SCRIPT=${ICS_HOME}/test/test_res.sh

################################################################################
# Functions
################################################################################
create_resource_file()
{
    resource_name=${1}
    echo "0" > ${RES_FILES}/${resource_name}
}

# Set a resource to be online
set_online()
{
    resource_name=${1}
    echo "1"  > ${RES_FILES}/${resource_name}
}

# Set a resource to be offline
set_offline()
{
    resource_name=${1}
    echo "0"  > ${RES_FILES}/${resource_name}
}

ics_reset()
{
    ${ICSSTOP}
    sleep 2
    rm ${ICS_CONFIG}
    rm ${RES_FILES}/* &> /dev/null
    ${ICSSTART}
    sleep 2
}
