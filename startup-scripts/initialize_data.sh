#!/bin/bash

set -e
cd $(readlink -e $(dirname "$0")/../)

# setup virtual env
[ ! -f ./env/bin/activate ] && (
    virtualenv -p python3 ./env
)
. ./env/bin/activate

python --version

# install app
pip install -U -r ./server/requirements.txt

# run
python manage.py app:initialize_data
