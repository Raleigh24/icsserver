#!/usr/bin/env bash

cmd=$1
resource=$2
time=$(date +%H:%M:%S)
resource_files=/home/raleigh/Development/PyCharmProjects/ICS2/var/test_resources

resource_online()
{
    resource_name=$1
    echo "1" > ${resource_files}/${resource_name}
}

resource_offline()
{
    resource_name=$1
    echo "0" > ${resource_files}/${resource_name}
}

get_resource_state()
{
    resource_name=$1
    state=$(cat ${resource_files}/${resource_name})
    #echo $state
    if [ "$state" -eq "1" ]; then
        exit 110
    else
        exit 100
    fi
}


case $cmd in
    "start") echo "${time} starting resource ${resource}";
            resource_online $resource;
            sleep 5;
            exit 0;;
    "stop")  echo "${time} stopping resource ${resource}";
             resource_offline $resource;
             sleep 5;
             exit 0;;
    "monitor")  echo "${time} monitoring resource ${resource}";
                sleep 5;
                get_resource_state $resource;;
    *) exit 1;;
esac
