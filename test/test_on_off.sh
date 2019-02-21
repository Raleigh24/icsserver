#!/usr/bin/env bash

export ICS_HOME=${ICS_HOME:-/opt/ICS}
source ${ICS_HOME}/test/test_setup.sh

while true; do
    ${ICSGRP} -online group-a
    sleep 30
    ${ICSGRP} -offline group-a
    sleep 30
done