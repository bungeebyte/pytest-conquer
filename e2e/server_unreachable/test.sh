#!/bin/bash
set -e

tox -e $1
ret=$?
if [ "$ret" != 3 ]; then
  echo "expected error code 3"
  exit 1
fi
exit 0
