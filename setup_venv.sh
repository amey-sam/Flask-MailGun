#!/bin/bash
set -x
venv_dir=venv_test
# rm -rdf $venv_dir # the no need to reinstall each time?
if [ ! -d "$venv_dir" ]; then
  virtualenv $venv_dir # TODO consider using --system-site-packages
fi
. $venv_dir/bin/activate
pip install pip-tools
pip-compile requirements.in
pip-compile requirements_dev.in
pip-compile requirements_test.in

pip install -r requirements.txt
pip install -r requirements_dev.txt
pip install -r requirements_test.txt
set +x
