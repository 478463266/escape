#!/usr/bin/env bash

## Test case header - START
# Get directory path of current test case
CWD="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get test case name
TEST_CASE="$( basename ${CWD} | tr '[:lower:]' '[:upper:]' )"
# Get ESCAPE command
ESCAPE="$( readlink -f ${CWD}/../../escape.py )"
# Print header
echo -e "\n==============================================================================="
echo -e "==                             TEST $TEST_CASE                                   =="
echo -e "===============================================================================\n"

# Print test case description
cat ${CWD}/README.txt
echo -e "\n===============================================================================\n"
echo
## Test case header - END

# Invoke ESCAPE here with test parameters
${ESCAPE} --debug --test --quit --log ${CWD}/escape.log --config ${CWD}/test.config --service ${CWD}/sapalias-test-req3.nffg