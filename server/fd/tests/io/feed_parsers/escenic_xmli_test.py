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
        with app.app_context():
            app.api_prefix = '/api'
            init_subjects(app)
            dirname = os.path.dirname(os.path.realpath(__file__))
            fixture = os.path.normpath(os.path.join(dirname, '../fixtures', 'simple-xmli.xml'))
            provider = {'name': 'Test'}
            with open(fixture, 'rb') as f:
                self.nitf = f.read()
                self.item = EscenicXMLIFeedParser().parse(etree.fromstring(self.nitf), provider)

    def test_parse_news_lines(self):
        self.assertEqual(self.item.get('headline'), 'Duisburg: So reagieren Gastronomen auf die Sperrstunde')
        self.assertEqual(self.item.get('slugline'), 'duisburg-so-reagieren-gastronomen-auf-die-sperrstunde-id230666788')
        self.assertEqual(self.item.get('copyrightline'), '(C) Funke Mediengruppe 2020')

    def test_parse_metadata(self):
        self.assertEqual(self.item.get('metadatatype'), 'FUNKE')
        self.assertEqual(self.item.get('authors'), [{'avatar_url': 'https://api.adorable.io/avatars/285/abott@adorable.png', 'role': 'writer', 'name': 'Fabienne Piepiora und Martin Schroers'}])
        self.assertEqual(self.item.get('extra'), {'waz_channel': 'Duisburg', 'kicker': 'Gastronomie', 'seo_title': 'Duisburg: So reagieren Gastronomen auf die Sperrstunde '})
        self.assertEqual(self.item.get('subject'), [{'scheme': 'paid_content', 'qcode': 'paid_content', 'parent': 'paid content', 'name': 'paid content'}])

    def test_feature_media(self):
        logger.info(self.item.get('associations'))
        expected = {'editor_1': {'creditline': 'copyright', 'renditions': {'original': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666784/2222538067-w1280-h960/9f9d47ee-0d6f-11eb-8036-08e03aada5c5.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}, 'thumbnail': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666784/2222538067-w1280-h960/9f9d47ee-0d6f-11eb-8036-08e03aada5c5.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}, 'viewImage': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666784/2222538067-w1280-h960/9f9d47ee-0d6f-11eb-8036-08e03aada5c5.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}, 'baseImage': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666784/2222538067-w1280-h960/9f9d47ee-0d6f-11eb-8036-08e03aada5c5.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}}, 'description_text': 'picture description', 'headline': 'picture', 'pubstatus': 'usable', 'guid': 'tag:img.waz.de:img:duisburg:origs230666784:2222538067-w1280-h960:9f9d47ee-0d6f-11eb-8036-08e03aada5c5.jpg', 'type': 'picture', 'mimetype': 'image/jpeg', 'alt_text': 'alt'}, 'featuremedia': {'creditline': 'FUNKE Foto Services', 'renditions': {'original': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666786/1212538474-w1280-h960/93594f24-0dfa-11eb-832f-e12cb3a7ec3d.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}, 'thumbnail': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666786/1212538474-w1280-h960/93594f24-0dfa-11eb-832f-e12cb3a7ec3d.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}, 'viewImage': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666786/1212538474-w1280-h960/93594f24-0dfa-11eb-832f-e12cb3a7ec3d.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}, 'baseImage': {'width': '1280', 'href': 'https://img.waz.de/img/duisburg/origs230666786/1212538474-w1280-h960/93594f24-0dfa-11eb-832f-e12cb3a7ec3d.jpg', 'poi': {'y': 328, 'x': 124}, 'CropTop': 0, 'mimetype': 'image/jpeg', 'height': '853'}}, 'description_text': 'Der „Fährmann“ in Duisburg-Neudorf hat gerade erst wiedereröffnet. Nun trifft die Betreiber die neue Sperrstunde.', 'headline': 'picture', 'pubstatus': 'usable', 'guid': 'tag:img.waz.de:img:duisburg:origs230666786:1212538474-w1280-h960:93594f24-0dfa-11eb-832f-e12cb3a7ec3d.jpg', 'type': 'picture', 'mimetype': 'image/jpeg', 'alt_text': 'alt text'}}
        self.assertEqual(self.item.get('associations'), expected)
    
    def test_news_identifier(self):
        self.assertEqual(self.item.get('guid'), 'urn:newsml:49:20201014:230666788:1')
        self.assertEqual(self.item.get('version'), '1')
        self.assertEqual(self.item.get('source_id'), '230666788')
        self.assertEqual(self.item.get('data'), '20201014')
    
    def test_byline(self):
        self.assertEqual(self.item.get('byline'), 'Fabienne Piepiora und Martin Schroers')
    
    def test_slugline(self):
        self.assertEqual(self.item.get('slugline'), 'duisburg-so-reagieren-gastronomen-auf-die-sperrstunde-id230666788')
        self.assertEqual(self.item.get('unique_name'), '#230666788')
        self.assertEqual(self.item.get('unique_id'), 230666788)

    def test_news_management(self):
        self.assertEqual(self.item.get('newsitemtype'), 'News Article')
        logger.info(self.item.get('firstcreated'))
        self.assertEqual(self.item.get('firstcreated'),  datetime.datetime.strptime('20201014T110403+0200', '%Y%m%dT%H%M%S%z'))
