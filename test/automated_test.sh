#!/usr/bin/env bash

export ICS_HOME=${ICS_HOME:-/opt/ICS}
source ${ICS_HOME}/test/test_setup.sh

################################################################################
# Test Case 1 - Basic online and offline
################################################################################
test_case_1()
{
    echo "1 - Testing basic online and offline"

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSGRP} -online group-a
    ${ICSGRP} -wait group-a ONLINE 120 || { echo "FAIL"; return; }
    ${ICSGRP} -offline group-a
    ${ICSGRP} -wait group-a OFFLINE 120 || { echo "FAIL"; return; }


    test "$(${ICSGRP} -state group-a)" == "OFFLINE" || { echo "FAIL"; return; }
    echo "PASS"
}


################################################################################
# Test Case 2 - Test resource Enable/Disable
################################################################################
test_case_2()
{
    echo "2 - Testing resource Enable/Disable"

    ics_reset
    ${ICS_HOME}/test/setup_basic_resource.sh 1> /dev/null

    ${ICSRES} -modify proc-a1 Enabled false
    ${ICSRES} -online proc-a1
    sleep 10

    test "$(${ICSRES} -state proc-a1)" == "OFFLINE" || { echo "FAIL"; return; }
    echo "PASS"
}

################################################################################
# Test Case 3 - Test Enable/Disable group
################################################################################
test_case_3()
{
    echo "3 - Testing group Enable/Disable"

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSGRP} -modify group-a Enabled false
    ${ICSGRP} -online group-a
    sleep 10

    test "$(${ICSGRP} -state group-a)" == "OFFLINE" || { echo "FAIL"; return; }
    echo "PASS"
}

################################################################################
# Test Case 4 - Test fault detection
################################################################################
test_case_4()
{
    echo "4 - Testing fault detection..."

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSGRP} -online group-a
    ${ICSGRP} -wait group-a ONLINE 120 || { echo "FAIL"; return; }

    set_offline proc-a1
    ${ICSRES} -probe proc-a1
    sleep 10
    ${ICSRES} -wait proc-a1 ONLINE 120 || { echo "FAIL"; return; }

    set_offline proc-a1
    ${ICSRES} -probe proc-a1
    sleep 10
    ${ICSRES} -wait proc-a1 ONLINE 120 || { echo "FAIL"; return; }

    set_offline proc-a1
    ${ICSRES} -probe proc-a1
    sleep 10

    test "$(${ICSRES} -state proc-a1)" == "FAULTED" || { echo "FAIL"; return; }
    echo "PASS"
}

################################################################################
# Test Case 5 - Test pass though propagation
################################################################################
test_case_5()
{
    echo "5 - Testing pass though propagation..."

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSRES} -modify proc-a3 Enabled false

    ${ICSGRP} -online group-a

    #${ICSGRP} -wait group-a ONLINE 120 || { echo "FAIL"; return; }
    sleep 60

    test "$(${ICSRES} -state proc-a1)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a2)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a3)" == "OFFLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a4)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a5)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a6)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a7)" == "ONLINE" || { echo "FAIL"; return; }
    echo "PASS"
}

################################################################################
# Test Case 6 - Test MonitorOnly attribute
################################################################################
test_case_6()
{
    echo "6 - Testing MonitorOnly attribute..."

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSRES} -modify proc-a3 MonitorOnly true

    ${ICSGRP} -online group-a

    sleep 60

    #${ICSGRP} -wait group-a ONLINE 120 || { echo "FAIL"; return; }

    test "$(${ICSRES} -state proc-a1)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a2)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a3)" == "OFFLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a4)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a5)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a6)" == "ONLINE" || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a7)" == "ONLINE" || { echo "FAIL"; return; }
    echo "PASS"
}

################################################################################
# Test Case 7 - Test AutoStart group attribute
################################################################################
test_case_7()
{
    echo "7 - Testing AutoStart group attribute..."

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSGRP} -modify group-a AutoStart true
    ${ICSSTOP}
    sleep 2
    ${ICSSTART}
    sleep 5
    ${ICSGRP} -wait group-a ONLINE 120 || { echo "FAIL"; return; }
    echo "PASS"

}

################################################################################
# Test Case 8 - Test IgnoreDisabled group attribute
################################################################################
test_case_8()
{
    echo "8 - Testing IgnoreDisabled group attribute..."

    ics_reset
    ${ICS_HOME}/test/setup_basic_group.sh 1> /dev/null

    ${ICSGRP} -modify group-a IgnoreDisabled true
    ${ICSRES} -modify proc-a7 Enabled false
    ${ICSGRP} -online group-a
    ${ICSGRP} -wait group-a ONLINE 120 || { echo "FAIL"; return; }
    test "$(${ICSRES} -state proc-a7)" == "OFFLINE" || { echo "FAIL"; return; }
    echo "PASS"
}


test_case=$1

case ${test_case} in
    1)  test_case_1;;
    2)  test_case_2;;
    3)  test_case_3;;
    4)  test_case_4;;
    5)  test_case_5;;
    6)  test_case_6;;
    7)  test_case_7;;
    8)  test_case_8;;
    *)
        test_case_1
        test_case_2
        test_case_3
        test_case_4
        test_case_5
        test_case_6
        test_case_7
        test_case_8
        ${ICSSTOP}  # Stop server after tests complete

    ;;
esac


