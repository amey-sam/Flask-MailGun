#!/bin/bash
set -x
venv_dir=venv_test
# rm -rdf $venv_dir # the no need to reinstall each time?
if [ ! -d "$venv_dir" ]; then
  virtualenv --system-site-packages $venv_dir # TODO consider using --system-site-packages
fi
. $venv_dir/bin/activate
pip install -r requirements.txt
set +x
