# -*- coding: utf-8; -*-
#
# This file is part of funke digital
#
# Copyright 2013-2018 Sourcefabric z.u. and contributors.
#
# For the full copyright and license information, please see the
# AUTHORS and LICENSE files distributed with this source code, or
# at https://www.sourcefabric.org/superdesk/license

import re
#import feedparser
import xmltodict
from lxml import etree
import requests

from superdesk.errors import IngestApiError, ParserError
from superdesk.io.registry import register_feeding_service, register_feeding_service_parser
from superdesk.io.feeding_services.http_base_service import HTTPFeedingServiceBase
from fd.io.feed_parsers.spoton_parser import EscenicSpotonFeedParser


class EscenicXMLIFeedingService(HTTPFeedingServiceBase):
    """
    Feeding Service class for FUNKE XMLI Feeding Service
    """

    NAME = 'spoton'
    ERRORS = [ParserError.parseMessageError().get_error_description()]

    label = 'Funke Spoton Service'

    fields = [
        {
            'id': 'url', 'type': 'text', 'label': 'News Sitemap URL',
            'placeholder': 'News Sitemap URL', 'required': True,
            'default': 'https://concast.airmotion.de/feed/B2qwTsDNd3aL1hOCJGJY1mtIMgEy1fqE'
        }
    ]
    HTTP_AUTH = False

    def __init__(self):
        super().__init__()

    def _test(self, provider=None):
        config = self.config
        url = config['url']

        self.get_url(url)

    def _update(self, provider=None, update=None):
        parsed_items = []

        try:
            parsed_items = self._fetch_data()
        except Exception as ex:
            raise ParserError.parseMessageError(ex, provider, data=parsed_items)
        return [parsed_items]

    def _fetch_data(self):
        url = self.config['url']
        response = requests.get(url)
        data = xmltodict.parse(response.content)
        items = []
        items = data['Feed']['NewsItems']
        for item in items[:50]:
            print(item)
            xml_elements = etree.fromstring(item)
            xmliparser = EscenicSpotonFeedParser()
            items.append(xmliparser.parse(xml_elements, self.provider))
                
        return items


register_feeding_service(EscenicSpotonFeedParser)
register_feeding_service_parser(EscenicSpotonFeedParser.NAME, None)
