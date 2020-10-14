#!/bin/bash
cd /opt/superdesk/ &&
python3 -m venv env && . env/bin/activate && pip install -Ur requirements.txt && . activate.sh
# find the config filename and replace it by our sd config, based on environment
cd /opt/superdesk/client 
#rm -rf ./dist/ ./node_modules/ &&
#npm install &&
#grunt build &&
find ./dist/ -maxdepth 1 -name "config.*.js" -exec cp "/opt/superdesk/client/$SUPERDESK_CLIENT_CONFIG_FILE" {} \;
#find ./dist/ -maxdepth 1 -name "config.*.js" -exec cp /opt/superdesk/client/superdesk-stage.cloud.config.js {} \;

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
