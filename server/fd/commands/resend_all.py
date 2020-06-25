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
from flask import current_app as app
from superdesk import get_resource_service
from superdesk.metadata.item import CONTENT_STATE, ITEM_STATE
from apps.archive.archive import SOURCE as ARCHIVE
from eve.utils import ParsedRequest, config, date_to_str
from apps.publish.enqueue.enqueue_service import EnqueueService

logger = logging.getLogger(__name__)


class ResendAll(superdesk.Command):
    option_list = [
        superdesk.Option('--etag', '-et', dest='etag', required=True),
        superdesk.Option('--list', '-f', dest='file', required=False),
    ]

    def run(self, etag, file):
        logger.info('Starting testing resend all command')
        self.etag = etag
        self.file = file
        self.ids = []
        try:
            with open(self.file, mode='r') as csv_file:
                self.ids = sum(list(csv.reader(csv_file)), [])

            self.fix_items_images()
        except:
            logger.exception('Failed to apply resend articles...')
            return 1

    def fix_items_images(self):
        """Fix the items images
        """
        logger.info('Fixing expired content.')
        for items in self.get_all_articles():
            for item in items:
                self.resend_items(item)

    def get_all_articles(self):
        logger.info('fetching all articles...')
        query = {
            ITEM_STATE: {'$in': [
                CONTENT_STATE.PUBLISHED,
                CONTENT_STATE.CORRECTED,
                CONTENT_STATE.KILLED,
                CONTENT_STATE.RECALLED
            ]}
        }

        req = ParsedRequest()
        req.sort = '[("unique_id", 1)]'
        req.where = json.dumps(query)
        cursor = get_resource_service(ARCHIVE).get_from_mongo(req=req, lookup=None)
        items = list(cursor)
        count = cursor.count()
        if count:
            yield items

    def resend_items(self, item):
        """Resend the item to the subscriber
        :param dict item:
        """
        logger.info(self.etag)
        self.service = EnqueueService()
        subscribers = [s for s in app.data.find_all('subscribers') if s['_etag'] == self.etag]

        if item['guid'] in self.ids:
            self.service.resend(item, subscribers)


superdesk.command('app:resend_all', ResendAll())
