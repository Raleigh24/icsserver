#!/usr/bin/env bash

export ICS_HOME=${ICS_HOME:-/opt/ICS}
source ${ICS_HOME}/test/test_common.sh

resource_list=$(${ICSRES} -list)
for resource in ${resource_list}; do
    echo "Deleting ${resource} ..."
    ${ICSRES} -delete ${resource}
done

group_list=$(${ICSGRP} -list)
for group in ${group_list}; do
    echo "Deleting ${group} ..."
    ${ICSGRP} -delete ${group}
done


