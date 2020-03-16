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

cd /opt/superdesk/client/dist &&
sed -i \
 -e "s/http:\/\/localhost:5000\/api/$(echo $SUPERDESK_URL | sed 's/\//\\\//g')/g" \
 -e "s/ws:\/\/localhost:5100/$(echo $SUPERDESK_WS_URL | sed 's/\//\\\//g')/g" \
 -e "s/ws:\/\/0.0.0.0:5100/$(echo $SUPERDESK_WS_URL | sed 's/\//\\\//g')/g" \
 -e 's/iframely:{key:""}/iframely:{key:"'$IFRAMELY_KEY'"}/g' \
 app*.js &&
nginx &

#cd /opt/superdesk && sleep 5 && bash honcho start
cd /opt/superdesk && bash ./scripts/fig_wrapper.sh honcho start


