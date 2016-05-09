#!/bin/bash
set -x
./setup_venv
. ./venv_test/bin/activate
export MAILGUN_API_KEY='testtesttest'
coverage run --source=. -m unittest discover
coverage xml
pylint -f parseable -d  | tee pylint.out
set +x
