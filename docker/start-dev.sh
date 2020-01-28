#!/bin/bash

cd /opt/superdesk/ &&
python3 -m venv env && . env/bin/activate && pip install -Ur dev-requirements.txt && . activate.sh &&

#  . /opt/superdesk/activate.sh && python3 manage.py app:flush_elastic_index --capi
#  . /opt/superdesk/activate.sh && python3 manage.py app:flush_elastic_index --sd


python3 manage.py app:initialize_data &&
python3 manage.py users:create -u admin -p admin -e 'admin@example.com' --admin

cd /opt/superdesk/client &&
npm install &&
grunt build

cd /opt/superdesk/client &&
grunt server --server='http://localhost:5000/api' --ws='ws://localhost:5100' &



cd /opt/superdesk &&
#honcho start
bash ./scripts/fig_wrapper.sh honcho start
