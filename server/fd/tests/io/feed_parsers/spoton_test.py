# -*- coding: utf-8; -*-
#
# This file is part of Superdesk.
#
# Copyright 2013, 2014 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import datetime
import os
import unittest
import flask
from pytz import utc

from superdesk.etree import etree
from fd.io.feed_parsers.spoton_parser import SpotonFeedParser
from superdesk.io.subjectcodes import init_app as init_subjects
from superdesk import get_resource_service

import logging

logger = logging.getLogger(__name__)


class SpotonParserTest(unittest.TestCase):
    def setUp(self):
        app = flask.Flask(__name__)
        with app.app_context():
            app.api_prefix = '/api'
            init_subjects(app)
            dirname = os.path.dirname(os.path.realpath(__file__))
            fixture = os.path.normpath(os.path.join(dirname, '../fixtures', 'spoton-feed.xml'))
            provider = {'name': 'Test'}
            with open(fixture, 'rb') as f:
                self.nitf = f.read()
                self.item = SpotonFeedParser().parse(etree.fromstring(self.nitf), provider)

    def test_parse_metadata(self):
        self.assertEqual(self.item['author'], [{'name': '(hub/spot)', 'role': 'writer', 'avatar_url': 'https://api.adorable.io/avatars/285/abott@adorable.png'}])
        self.assertEqual(self.item['version'], 1)
        self.assertEqual(self.item['priority'], 3)
        self.assertEqual(self.item['format'], 'STD')
        self.assertEqual(self.item['type'], 'article')
        self.assertEqual(self.item['keywords'], ['Christina Stürmer', 'Schwangerschaft', 'Oliver Varga', 'Instagram'])
        #self.assertEqual(self.item['versioncreated'], datetime.datetime.strptime('Tue, 20 Oct 2020 09:39:41 +0000', '%a, %d %b %Y %H:%M:%S %z'))
        self.assertEqual(self.item['extra'], {'department': 'People', 'location': 'AT', 'sub_headline': 'Zweites Kind für die Sängerin'})
        self.assertEqual(self.item['headline'], 'Christina Stürmer wird erneut Mutter')
