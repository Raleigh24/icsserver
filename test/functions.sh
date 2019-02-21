#!/usr/bin/env bash

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
