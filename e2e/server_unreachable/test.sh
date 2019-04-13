#!/bin/bash
set -ev

tox -e $1

ret=$?
if [ "$ret" != 3 ]; then
  echo "expected error code 3, but it's $ret"
  exit 1
fi

exit 0
