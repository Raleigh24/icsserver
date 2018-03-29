#! /bin/bash

ICSRES=../bin/icsres
ICSGRP=../bin/icsgrp
resource_files=/home/raleigh/Development/PyCharmProjects/ICS2/var/test_resources
RES_SCRIPT="/home/raleigh/Development/PyCharmProjects/ICS2/test/test_res.sh"
grp_res_count=300
resourceID=$(seq 1 1 $grp_res_count)


create_resource_file()
{
    resource_name=$1
    echo "0" > ${resource_files}/${resource_name}
}

for letter in {a..z}; do
	group_name=group-${letter}
	echo "Creating group ${group_name}"
	$ICSGRP -add $group_name
	for resource in $resourceID; do 
		resource_name=proc-${letter}${resource}
		echo "Creating resource ${resource_name}" 
		create_resource_file $resource_name
		$ICSRES -add $resource_name $group_name
                $ICSRES -modify $resource_name StartProgram "${RES_SCRIPT} start ${resource_name}"
                $ICSRES -modify $resource_name StopProgram "${RES_SCRIPT} stop ${resource_name}"
                $ICSRES -modify $resource_name MonitorProgram "${RES_SCRIPT}  monitor ${resource_name}"
		#sleep 0.5
	done
	$ICSGRP -enable $group_name
done







 
