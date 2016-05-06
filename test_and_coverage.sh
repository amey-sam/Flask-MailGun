#!/bin/bash
set -x
venv_dir=venv_test
# rm -rdf venv_test # the no need to reinstall each time?
if [ ! -d "$venv_dir" ]; then
  virtualenv  $venv_dir # TODO consider using --system-site-packages
fi
. $venv_dir/bin/activate
pip install -r requirements.txt
pip install -r requirements_test.txt
coverage run --source=. -m unittest discover
coverage xml
pylint -f parseable -d  | tee pylint.out
set +x
