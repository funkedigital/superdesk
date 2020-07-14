#!/bin/bash
# http://redsymbol.net/articles/unofficial-bash-strict-mode/
set -exuo pipefail

export DEBIAN_FRONTEND=noninteractive
export DBUS_SESSION_BUS_ADDRESS=/dev/null

_activate() {
    set +ux
    . /opt/superdesk/activate.sh
    set -ux
}

_missing_db() {
    curl -sI $ELASTICSEARCH_URL/$ELASTICSEARCH_INDEX | grep -q 404
}

_skip_install() {
    dpkg -l | grep '^ii.*'$1 && [ -z ${pkg_upgrade:-''} ]
}
### databases
# redis
if ! _skip_install redis-server; then
    apt -y install software-properties-common
    add-apt-repository -y ppa:chris-lea/redis-server
    apt -y update
    apt -y install --no-install-recommends redis-server || (
        # seems for some systems we must disable PrivateDevices,
        # otherwise redis fails on starting
        # https://bugs.launchpad.net/ubuntu/+source/redis/+bug/1663911
        path=/etc/systemd/system/redis-server.service.d
        mkdir $path
        echo '[Service]' > $path/redis.override.conf
        echo 'PrivateDevices=no' >> $path/redis.override.conf
    )

    systemctl enable redis-server
    systemctl restart redis-server
fi

# mongo
if ! _skip_install mongodb-org-server; then
    apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 2930ADAE8CAF5059EE73BB4B58712A2291FA4AD5
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.6 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.6.list

    apt -y update
    apt -y install --no-install-recommends \
        mongodb-org-server \
        mongodb-org-shell \
        mongodb-org-tools
fi

# tune mongo
cfg=/etc/mongod.conf
[ -f "${cfg}.bak" ] || mv $cfg $cfg.bak
cat <<EOF > $cfg
storage:
  dbPath: /var/lib/mongodb
  journal:
    enabled: true
  engine: wiredTiger

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

net:
  port: 27017
  bindIp: 0.0.0.0
EOF
unset cfg
systemctl enable mongod
systemctl restart mongod


# elasticsearch
wait_elastic() {
    elastic=0
    while [ $elastic -eq 0 ]
    do
        curl -s "http://localhost:9200" 2>&1 > /dev/null \
            && elastic=1 \
            || echo "waiting for elastic..."
        sleep .5
    done
}
if ! _skip_install elasticsearch; then
    wget --continue https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.6/elasticsearch-2.4.6.deb
    wget https://download.elastic.co/elasticsearch/release/org/elasticsearch/distribution/deb/elasticsearch/2.4.6/elasticsearch-2.4.6.deb.sha1 -O elasticsearch-2.4.6.deb.sha1
    echo "  elasticsearch-2.4.6.deb" >>elasticsearch-2.4.6.deb.sha1
    sha1sum -c elasticsearch-2.4.6.deb.sha1 && dpkg -i elasticsearch-2.4.6.deb
    apt -y update
    apt -y install --no-install-recommends openjdk-8-jre-headless
fi

# tune elasticsearch
cfg='/etc/elasticsearch/elasticsearch.yml'
[ -f "${cfg}.bak" ] || mv $cfg $cfg.bak
es_backups=/var/tmp/elasticsearch
if [ ! -d "$es_backups" ]; then
    mkdir $es_backups
    chown elasticsearch:elasticsearch $es_backups
fi
cat <<EOF > $cfg
network.bind_host: 0.0.0.0
node.local: true
discovery.zen.ping.multicast: false
path.repo: $es_backups
index.number_of_replicas: 0
EOF

systemctl enable elasticsearch
systemctl restart elasticsearch
wait_elastic

curl -s -XPUT 'http://localhost:9200/_snapshot/backups' \
    -d '{"type": "fs", "settings": {"location": "'$es_backups'"}}'
unset cfg es_backups


### build
locale-gen en_US.UTF-8

[ -d /var/log/superdesk ] || mkdir -p /var/log/superdesk
systemctl disable rsyslog
systemctl stop rsyslog

cat <<"EOF" > /etc/logrotate.d/superdesk
/var/log/superdesk/*.log {
    rotate 7
    daily
    missingok
    copytruncate
    notifempty
    nocompress
    size 20M
}
EOF
logrotate /etc/logrotate.conf

apt update
apt -y install --no-install-recommends \
git python3 python3-dev python3-venv \
build-essential libffi-dev \
libtiff5-dev libjpeg8-dev zlib1g-dev \
libfreetype6-dev liblcms2-dev libwebp-dev \
curl libfontconfig libssl-dev \
libxml2-dev libxslt1-dev \
libxmlsec1-dev

# node & npm
if ! _skip_install nodejs; then
    curl -sL https://deb.nodesource.com/setup_7.x | bash -
    apt install -y nodejs

    npm install -g grunt-cli
fi

node --version
npm --version
grunt --version

## virtualenv and activate script
env=/opt/superdesk/env
[ -d $env ] && rm -rf $env
python3 -m venv $env
unset env

cat <<"EOF" > /opt/superdesk/activate.sh
. /opt/superdesk/env/bin/activate

set -a
LC_ALL=en_US.UTF-8

# some settings required by client
PATH=/opt/superdesk/client/node_modules/.bin/:$PATH
SUPERDESK_URL='http://localhost/api'
SUPERDESK_WS_URL='ws://localhost/ws'
set +a
EOF

_activate
pip install -U pip wheel

## prepare source code
repo=${repo:-'/opt/superdesk'}
[ -d $repo ] || mkdir $repo
cd $repo
if [ ! -d $repo/.git ]; then
    git init .
    git remote add -t \* -f origin https://github.com/funkedigital/superdesk-fd
    git checkout 'stage-env' 
fi

cd /opt/superdesk/server
[ -f dev-requirements.txt ] && req=dev-requirements.txt || req=requirements.txt
time pip install -U -r $req

cd /opt/superdesk/client
time npm install


### deploy
cat <<"EOF" > /opt/superdesk/activate.sh
# you could write variables to /opt/superdesk/env.sh
. /opt/superdesk/env/bin/activate

set -a
LC_ALL=en_US.UTF-8
PYTHONUNBUFFERED=1
PATH=/opt/superdesk/client/node_modules/.bin/:$PATH

[ ! -f /opt/superdesk/env.sh ] || . /opt/superdesk/env.sh

HOST=${HOST:-'localhost'}
HOST_SSL=${HOST_SSL:-}
DB_HOST=${DB_HOST:-'localhost'}
DB_NAME=${DB_NAME:-'superdesk'}

[ -n "${HOST_SSL:-}" ] && SSL='s' || SSL=''
# To work properly inside and outside container, must be
# - "proxy_set_header Host <host>;" in nginx
# - the same "<host>" for next two settings
# TODO: try to fix at backend side, it should accept any host
SUPERDESK_URL="http$SSL://$HOST/api"
CONTENTAPI_URL="http$SSL://$HOST/contentapi"
SUPERDESK_WS_URL="ws$SSL://$HOST/ws"
SUPERDESK_CLIENT_URL="http$SSL://$HOST"

MONGO_URI="mongodb://$DB_HOST/$DB_NAME"
LEGAL_ARCHIVE_URI="mongodb://$DB_HOST/${DB_NAME}_la"
ARCHIVED_URI="mongodb://$DB_HOST/${DB_NAME}_ar"
ELASTICSEARCH_URL="http://$DB_HOST:9200"
ELASTICSEARCH_INDEX="$DB_NAME"

CONTENTAPI_ELASTICSEARCH_INDEX="${DB_NAME}_ca"
# TODO: fix will be in 1.6 release, keep it for a while
CONTENTAPI_ELASTIC_INDEX=$CONTENTAPI_ELASTICSEARCH_INDEX
CONTENTAPI_MONGO_URI="mongodb://$DB_HOST/${CONTENTAPI_ELASTICSEARCH_INDEX}"

REDIS_URL=${REDIS_URL:-redis://$DB_HOST:6379/1}

C_FORCE_ROOT=1
CELERYBEAT_SCHEDULE_FILENAME=${CELERYBEAT_SCHEDULE_FILENAME:-/tmp/celerybeatschedule}
CELERY_BROKER_URL=${CELERY_BROKER_URL:-$REDIS_URL}

if [ -n "$AMAZON_CONTAINER_NAME" ]; then
    AMAZON_S3_SUBFOLDER=${AMAZON_S3_SUBFOLDER:-'superdesk'}
    MEDIA_PREFIX=${MEDIA_PREFIX:-"http$SSL://$HOST/api/upload-raw"}

    # TODO: remove after full adoption of MEDIA_PREFIX
    AMAZON_SERVE_DIRECT_LINKS=${AMAZON_SERVE_DIRECT_LINKS:-True}
    AMAZON_S3_USE_HTTPS=${AMAZON_S3_USE_HTTPS:-True}
fi

if [ -n "${SUPERDESK_TESTING:-}" ]; then
    SUPERDESK_TESTING=True
    CELERY_ALWAYS_EAGER=True
    ELASTICSEARCH_BACKUPS_PATH=/var/tmp/elasticsearch
    LEGAL_ARCHIVE=True
fi
set +a
EOF

_activate


[ -z "${prepopulate-1}" ] || (
### prepopulate
_activate
cd /opt/superdesk/server

_sample_data() {
    sample_data=${sample_data:-}
    [ -z "$sample_data" ] || sample_data='--sample-data'
    (python manage.py app:initialize_data --help | grep -- --sample-data) && sample_data=$sample_data || sample_data=
}

if _missing_db; then
    _sample_data
    python manage.py app:initialize_data $sample_data
    python manage.py users:create -u admin -p admin -e 'admin@example.com' --admin
else
    python manage.py app:initialize_data
fi
unset sample_data
)

[ -z "${grunt_build-1}" ] || (
cd /opt/superdesk/client
time grunt build --webpack-no-progress
)

# Use latest honcho with --no-colour option
pip install -U honcho gunicorn

gunicorn_opts='-t 300 -w 1 --access-logfile=- --access-logformat="%(m)s %(U)s status=%(s)s time=%(T)ss size=%(B)sb"'
cat <<EOF > /opt/superdesk/server/Procfile
logs: journalctl -u superdesk* -f >> /var/log/superdesk/main.log
rest: gunicorn -b 0.0.0.0:5000 wsgi $gunicorn_opts
wamp: python3 -u ws.py
work: celery -A worker worker -c 1
beat: celery -A worker beat --pid=
capi: gunicorn -b 0.0.0.0:5400 content_api.wsgi $gunicorn_opts
EOF


cat <<"EOF" > /etc/systemd/system/superdesk.service
[Unit]
Description=superdesk
Wants=network.target
After=network.target

[Service]
ExecStart=/bin/sh -c '. /opt/superdesk/activate.sh && exec honcho start --no-colour'
WorkingDirectory=/opt/superdesk/server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
systemctl enable superdesk
systemctl restart superdesk

# nginx
if ! _skip_install nginx; then
    curl -s http://nginx.org/keys/nginx_signing.key | apt-key add -
    echo "deb http://nginx.org/packages/ubuntu/ xenial nginx" \
        > /etc/apt/sources.list.d/nginx.list

    apt -y update
    apt -y install nginx
fi

path=/etc/nginx/conf.d
cat <<EOF > $path/default.conf
server {
    listen 80 default;

    include $path/*.inc;
}
EOF
cat <<EOF > $path/default.inc
location /ws {
    proxy_pass http://localhost:5100;
    proxy_http_version 1.1;
    proxy_buffering off;
    proxy_read_timeout 3600;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "Upgrade";
}

location /api {
    proxy_pass http://localhost:5000;
    proxy_set_header Host $HOST;
    expires epoch;

    sub_filter_once off;
    sub_filter_types application/json;
    sub_filter 'http://localhost' 'http://\$host';
}

location /contentapi {
    proxy_pass http://localhost:5400;
    proxy_set_header Host $HOST;
    expires epoch;
}

location /.well-known {
    root /var/tmp;
}
location / {
    root /opt/superdesk/client/dist;

    # TODO: use "config.js:server" for user installations
    sub_filter_once off;
    sub_filter_types application/javascript;
    sub_filter 'http://localhost' 'http://\$host';
    sub_filter 'ws://localhost/ws' 'ws://\$host/ws';
}
EOF
cat <<"EOF" > $path/params.conf
tcp_nopush on;
tcp_nodelay on;
output_buffers 1 256k;
postpone_output 0;
keepalive_requests 210;
reset_timedout_connection on;
ignore_invalid_headers  on;
server_tokens off;
client_max_body_size 1024m;
recursive_error_pages   on;
server_name_in_redirect off;

gzip on;
gzip_disable "msie6";
gzip_vary on;
gzip_proxied any;
gzip_comp_level 1;
gzip_buffers 16 8k;
gzip_http_version 1.1;
gzip_types text/plain text/css application/json application/x-javascript application/javascript text/xml application/xml application/xml+rss text/javascript;

proxy_set_header Host $host;
proxy_set_header X-Forwarded-For $remote_addr;
proxy_set_header Accept-Encoding "";
proxy_buffering on;
proxy_ignore_client_abort off;
proxy_intercept_errors on;
proxy_next_upstream error timeout invalid_header;
proxy_redirect off;
proxy_buffer_size 32k;
proxy_buffers 8 32k;
proxy_busy_buffers_size 64k;
proxy_temp_file_write_size 64k;
client_body_buffer_size 128k;
proxy_connect_timeout 1;
proxy_send_timeout 300;
proxy_read_timeout 300;
proxy_cache_min_uses 1;
proxy_temp_path /var/tmp;
EOF
unset path
systemctl enable nginx
systemctl restart nginx


[ -z "${smtp-1}" ] || (
mails=/var/log/superdesk/mail
mkdir -p $mails

smtp_py=/var/tmp/smtp.py
cat <<EOF > $smtp_py
import argparse
import asyncore
import datetime as dt
import logging
import random
import smtpd
from email.parser import Parser
from pathlib import Path

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    datefmt='[%Y-%m-%d %H:%M:%S %Z]',
    format='%(asctime)s %(message)s'
)


class Server(smtpd.SMTPServer, object):
    """Logging-enabled SMTPServer instance."""

    def __init__(self, path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path = Path(path)
        path.mkdir(exist_ok=True)
        self._path = path

    def process_message(self, peer, mailfrom, rcpttos, data):
        msg = Parser().parsestr(data)
        subject = msg['subject']
        log.info('to=%r subject=%r', rcpttos, subject)
        for addr in rcpttos:
            name = (
                '{0:%Y%V/%w-%H%M%S}-{1:02d}-{2}.log'
                .format(dt.datetime.now(), random.randint(0, 99), addr)
            )
            log.info('filename=%r to=%r subject=%r', name, addr, subject)
            email = self._path / name
            email.parent.mkdir(exist_ok=True)
            email.write_text(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run an SMTP server.')
    parser.add_argument('addr', help='addr to bind to')
    parser.add_argument('port', type=int, help='port to bind to')
    parser.add_argument('path', help='directory to store to')
    args = parser.parse_args()

    log.info('Starting SMTP server at {0}:{1}'.format(args.addr, args.port))
    server = Server(args.path, (args.addr, args.port), None)
    try:
        asyncore.loop()
    except KeyboardInterrupt:
        log.info('Cleaning up')
EOF

cat <<EOF >> /etc/nginx/conf.d/default.inc
location /mail {
    alias $mails/;
    default_type text/plain;
    autoindex on;
    autoindex_exact_size off;
}
EOF

service=superdesk-smtp
cat <<EOF > /etc/systemd/system/$service.service
[Unit]
Description=Dev SMTP server for superdesk, it doesn't send real emails
Wants=network.target
After=network.target

[Service]
ExecStart=/bin/sh -c '. /opt/superdesk/env/bin/activate && exec python3 $smtp_py localhost 25 $mails'
WorkingDirectory=/opt/superdesk
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl enable $service
systemctl restart $service

nginx -s reload
unset smtp_py mails
)