#!/bin/bash

cd /opt/superdesk/ &&
python3 -m venv env && . env/bin/activate && . activate.sh

#  . /opt/superdesk/activate.sh && python3 manage.py app:flush_elastic_index --capi
#  . /opt/superdesk/activate.sh && python3 manage.py app:flush_elastic_index --sd

# python3 manage.py app:initialize_data &&
# python3 manage.py users:create -u admin -p admin -e 'admin@example.com' --admin
