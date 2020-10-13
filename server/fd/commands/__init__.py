# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

from .resend_all import ResendAll  # noqa
from .update_content_lists import UpdateContentLists  # noqa
from superdesk.celery_app import celery
from superdesk.default_settings import celery_queue
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def init_app(app):
    app.config['CELERY_TASK_ROUTES']['fd.commands.updatecl'] = {
                'queue': celery_queue('expiry'),
                'routing_key': 'expiry.updatecl'
            }

    app.config['CELERY_BEAT_SCHEDULE']['planning:updatecl'] = {
                'task': 'fd.commands.updatecl',
                'schedule': timedelta(seconds=1)
            }


@celery.task(soft_time_limit=1)
def updatecl():
    UpdateContentLists().run()