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
from superdesk import get_resource_service

import logging

logger = logging.getLogger(__name__)


class EscenicXMLIFeedParserTest(unittest.TestCase):
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

    def test_paywall(self):
        pass

    def test_parse_media(self):
        expected = {
            'featuremedia': {
                'renditions': {
                    'baseImage': {
                        'width': '1080', 'mimetype': 'image/jpeg', 'height': '462',
                        'href': 'https://img.waz.de/img/panorama/crop228775111/282185123-w1080-cv21_9-q85/5889202e-6eb1-11ea-8a53-d3fa31c35829.jpg'
                    },
                    'viewImage': {
                        'width': '1080', 'mimetype': 'image/jpeg', 'height': '462',
                        'href': 'https://img.waz.de/img/panorama/crop228775111/282185123-w1080-cv21_9-q85/5889202e-6eb1-11ea-8a53-d3fa31c35829.jpg'
                    }
                },
                'type': 'picture',
                'headline': 'Dieb schlägt Autoscheibe ein – und klaut Klopapier',
                'guid': 'tag:img.waz.de:img:panorama:crop228775111:282185123-w1080-cv21_9-q85:5889202e-6eb1-11ea-8a53-d3fa31c35829.jpg',
                'creditline': 'imago stockpeople',
                'description_text': 'Ein Dieb hat in Kiel eine Autoscheibe eingeschlagen, um Bohrschrauber und Toilettenpapier mitgehen zu lassen. (Symbolbild)'
            }
        }

        self.assertEqual(self.item.get('associations'), expected)

    def test_parse_byline(self):
        self.assertEqual(self.item.get('byline'), '')

    def test_is_paid_content(self):
        expected = {
            'name': 'paid content',
            'parent': 'paid content',
            'qcode': 'paid_content',
            'scheme': 'paid_content',
        }
        self.assertEqual(self.item.get('subject')[0], expected)

    def test_parse_news_identifier(self):
        self.assertEqual(self.item.get('guid'), 'urn:newsml:49:20200325:228775113:1')
        self.assertEqual(self.item.get('version'), '1')
        self.assertEqual(self.item.get('source_id'), '228775113')
        self.assertEqual(self.item.get('data'), '20200325')

    def test_parse_newslines(self):
        self.assertEqual(self.item.get('headline'), 'Dieb schlägt Autoscheibe ein – und klaut Klopapier')
        self.assertEqual(self.item.get('slugline'), 'Polizei')
        self.assertEqual(self.item.get('copyrightline'), '(C) Funke Mediengruppe 2020')

    def test_parse_metadata(self):
        self.assertEqual(self.item.get('copyrightline'), '(C) Funke Mediengruppe 2020')
        self.assertEqual(self.item.get('metadatatype'), 'FUNKE')
