#! /bin/bash

HARES=../bin/icsres
VG_SCID_LIST="4529"

letters="a b c d e f g"
group="vg-abc"

for letter in $letters; do 
	resource=proc-${letter}
	echo "Creating resource ${resource}" 
	$HARES -add $resource $group
done


echo "Creating dependancy links"
$HARES -link proc-a proc-b
$HARES -link proc-a proc-c
$HARES -link proc-b proc-e
$HARES -link proc-b proc-d
$HARES -link proc-c proc-f
$HARES -link proc-c proc-g



# Enable all resources
#for node in ${CLUSTER_NODE[@]} ; do
#	$HAGRP -enable vg-waterr -sys $node > /dev/null 2>&1
#done



 
