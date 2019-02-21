#!/usr/bin/env bash

export ICS_HOME=${ICS_HOME:-/opt/ICS}

ICSSTART=${ICS_HOME}/bin/icsstart
ICSSTOP=${ICS_HOME}/bin/icsstop
ICSRES=${ICS_HOME}/bin/icsres
ICSGRP=${ICS_HOME}/bin/icsgrp
ICSSYS=${ICS_HOME}/bin/icssys

ICS_VAR=/var/opt/ics
ICS_CONFIG=${ICS_VAR}/config/main.cf

RES_FILES=${ICS_VAR}/test_resources
RES_SCRIPT=${ICS_HOME}/test/test_res.sh

source ${ICS_HOME}/test/functions.sh
