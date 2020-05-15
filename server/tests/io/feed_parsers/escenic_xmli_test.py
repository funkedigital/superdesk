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
from fd.io.feed_parsers.escenic_xmli import EscenicXMLIFeedParser
from superdesk.io.subjectcodes import init_app as init_subjects


class BaseXMLITestCase(unittest.TestCase):
    def setUp(self):
        app = flask.Flask(__name__)
        app.api_prefix = '/api'
        init_subjects(app)
        dirname = os.path.dirname(os.path.realpath(__file__))
        fixture = os.path.normpath(os.path.join(dirname, '../fixtures', 'simple-xmli.xml'))
        provider = {'name': 'Test'}
        with open(fixture, 'rb') as f:
            self.nitf = f.read()
            self.item = EscenicXMLIFeedParser().parse(etree.fromstring(self.nitf), provider)

class ReutersTestCase(BaseXMLITestCase):
    def test_content(self):
        self.assertEqual(self.item.get('headline'), "Dieb schlägt Autoscheibe ein – und klaut Klopapier")
        self.assertEqual(self.item.get('guid'), 'urn:newsml:49:20200325:228775113:1')
        self.assertEqual(self.item.get('url'), 'https://www.waz.de/panorama/autoknacker-schlaegt-scheibe-ein-und-klaut-klopapier-id228775113.html')
        self.assertEqual(self.item.get('firstcreated').isoformat(), '2020-03-25T16:59:15')
        self.assertTrue(self.item.get('body_html').startswith('\n<p class="intro">\n'))

    def test_coreitemvalues(self):
        self.assertEqual(self.item.get('newsitemtype'), 'News Article')
        self.assertEqual(self.item.get('version'), '1')
        self.assertEqual(self.item.get('versioncreated'), datetime.datetime(2020, 3, 25, 16, 59, 12))
