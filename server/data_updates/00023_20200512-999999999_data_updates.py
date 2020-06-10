# -*- coding: utf-8; -*-
# This file is part of Superdesk.
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license
#
# Author  : root
# Creation: 2020-05-12 06:03

from superdesk.commands.data_updates import DataUpdate

METADATA = {
    'advertising': {
        'scheme': 'seo_metadata',
        'qcode': 'advertising',
        'parent': 'advertising',
        'name': 'advertising',
    },
    'noIndex': {
        'scheme': 'seo_metadata',
        'qcode': 'no_index',
        'parent': 'no index',
        'name': 'no index / no follow',
    },
    'allowComments': {
        'scheme': 'seo_metadata',
        'qcode': 'allow_comments',
        'parent': 'allow comments',
        'name': 'allow comments',
    }
}

FLAGS = {
    'marked_archived_only': False,
    'marked_for_legal': False,
    'marked_for_sms': False,
    'marked_for_not_publication': False
}


class DataUpdate(DataUpdate):
    resource = 'archive'

    def forwards(self, mongodb_collection, mongodb_database):

        for archive in mongodb_collection.find({}):
            sub = []
            article_id = archive['_id']
            flags = archive['flags']
            for x in flags:
                if METADATA.get(x) and flags[x] == True:
                    sub.append(METADATA.get(x))
            mongodb_collection.update({'_id': article_id}, {
                '$set': {'subject': sub, 'flags': FLAGS}
            })

    def backwards(self, mongodb_collection, mongodb_database):
        pass
