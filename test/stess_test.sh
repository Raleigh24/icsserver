#! /bin/bash

export ICS_HOME=${ICS_HOME:-/opt/ICS}
source ${ICS_HOME}/test/test_setup.sh

grp_res_count=300  # Number of resources per group
resource_id=$(seq -w 1 1 ${grp_res_count})

create_resource_file()
{
    resource_name=${1}
    echo "0" > ${RES_FILES}/${resource_name}
}

for letter in {a..g}; do
	group_name=group-${letter}
	echo "Creating group ${group_name}"
	${ICSGRP} -add ${group_name}
	for resource in ${resource_id}; do
		resource_name=proc-${letter}${resource}
		echo "Creating resource ${resource_name}" 
		create_resource_file ${resource_name}
		${ICSRES} -add ${resource_name} ${group_name}
                ${ICSRES} -modify ${resource_name} StartProgram "${RES_SCRIPT} start ${resource_name}"
                ${ICSRES} -modify ${resource_name} StopProgram "${RES_SCRIPT} stop ${resource_name}"
                ${ICSRES} -modify ${resource_name} MonitorProgram "${RES_SCRIPT}  monitor ${resource_name}"
		#sleep 0.5
	done
	${ICSGRP} -enable ${group_name}
done







 
