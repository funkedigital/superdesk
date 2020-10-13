# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license
import logging
import json
import csv
import superdesk
import requests
import os
from flask import current_app as app
from superdesk import get_resource_service
from superdesk.metadata.item import CONTENT_STATE, ITEM_STATE
from apps.archive.archive import SOURCE as ARCHIVE
from eve.utils import ParsedRequest, config, date_to_str
from apps.publish.enqueue.enqueue_service import EnqueueService
from superdesk.celery_task_utils import get_lock_id
from superdesk.lock import lock, unlock
logger = logging.getLogger(__name__)


class UpdateContentLists(superdesk.Command):
    option_list = [
    ]


    def run(self):

        publisher_domain = os.environ.get('PUBLISHER_DOMAIN', '') # https://www.wmn.de
        token = os.environ.get('API_KEY', '')

        if len(publisher_domain) == 0 or len(token) == 0:
            logger.info('pubisher domain or api key are not set')
            return

        logger.info('Starting updating Content List.')
        lock_name = get_lock_id('planning', 'updatecl')
        if not lock(lock_name, expire=610):
            logger.info('{} Updating Content List task is already running')
            return
        req = requests.get(publisher_domain + '/api/v2/content/lists/?limit=99999', headers={'Authorization': 'Basic ' + token})
        if req.status_code == 200:
            for b in req.json()['_embedded']['_items']:
                url = publisher_domain + '/api/v2/content/lists/' + str(b['id'])
                payload = {'filters': b['filters']}
                headers = {'Authorization': 'Basic ' + token}
                requests.post(url, json=json.dumps(payload), headers=head)
        logger.info('content lists are updated')
        unlock(lock_name)

superdesk.command('app:updatecl', UpdateContentLists())
