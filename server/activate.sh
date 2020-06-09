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

MONGO_URI="mongodb://mongodb/superdesk"
LEGAL_ARCHIVE_URI="mongodb://mongodb/superdesk_la"
ARCHIVED_URI="mongodb://mongodb/superdesk_ar"
ELASTICSEARCH_URL="http://elastic:9200"
ELASTICSEARCH_INDEX="superdesk"

CONTENTAPI_ELASTICSEARCH_INDEX="superdesk_ca"
# TODO: fix will be in 1.6 release, keep it for a while
CONTENTAPI_ELASTIC_INDEX=$CONTENTAPI_ELASTICSEARCH_INDEX
CONTENTAPI_MONGO_URI="mongodb://mongodb/${CONTENTAPI_ELASTICSEARCH_INDEX}"

REDIS_URL=${REDIS_URL:-redis://redis:6379/1}

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
