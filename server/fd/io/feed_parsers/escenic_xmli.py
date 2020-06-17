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
import logging
import lxml.html

from flask import current_app as app
from superdesk.errors import ParserError
from superdesk.io.registry import register_feed_parser
from superdesk.io.feed_parsers import XMLFeedParser
from superdesk.media.renditions import update_renditions
from superdesk.metadata.item import ITEM_TYPE, CONTENT_TYPE, GUID_FIELD
from superdesk.metadata.utils import is_normal_package
from superdesk.utc import utc
from lxml import etree
from superdesk.io.feeding_services.rss import RSSFeedingService, generate_tag_from_url

logger = logging.getLogger(__name__)


class EscenicXMLIFeedParser(XMLFeedParser):
    """
    Feed Parser for Funke Escenic XMLI
    """

    NAME = 'ecexmli'

    label = 'Escenic XMLI Parser'

    def can_parse(self, xml):
        return xml.tag == 'NewsML'

    def parse(self, xml, provider=None):
        items = {}
        try:
            self.parse_newslines(items, xml)
            self.parse_media(items, xml)
            self.parse_news_identifier(items, xml)
            self.parse_metadata(items, xml)
            self.parse_byline(items, xml)
            self.parse_news_management(items, xml)
            self.parse_body_html(items, xml)

            return items
        except Exception as ex:
            raise ParserError.newsmlTwoParserError(ex, provider)

    # TODO check internal links like /12345656 (escenic id) and look for <NewsItemId>229126224</NewsItemId> in source_id
    # relative links to category pages /sport/football and absolute links remain untouched

    def parse_media(self, xml):
        root = lxml.html.fromstring(xml)
        for action, el in etree.iterwalk(root):
            if el.tag == 'media':
                for br in el.xpath('.'):
                    self.transform_media_tag(br)
                    br.tail = 'CHANGE THIS' + br.tail
                    br.drop_tree()
        return etree.tostring(root)
    
    def parse_body_html(self, items, tree):
        """ parses the elements of the body """
        body_xml = etree.tostring(
            tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.content'),
            encoding='unicode').replace('<body.content>', '').replace('</body.content>', '')

        # transform the media elements
        #body_xml = self.parse_media(body_xml)

        items['body_html'] = body_xml

    def parse_media(self, items, tree):
        parsed_media = self.media_parser(
            tree.findall('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.content/media/'))
        items['associations'] = {
            'featuremedia': {
                'type': 'picture',
                'guid': generate_tag_from_url(parsed_media[0]['source']),
                'headline': items['headline'],
                'creditline': parsed_media[0]['copyright'],
                'description_text': parsed_media[0]['alternate-text'],
                # 'firstcreated': items['versioncreated'],
                # 'versioncreated': items['versioncreated'],
                'renditions': {
                    'baseImage': {
                        'href': parsed_media[0]['source'],
                        'width': parsed_media[0]['width'],
                        'height': parsed_media[0]['height'],
                        'mimetype': 'image/jpeg',
                    },
                    'viewImage': {
                        'href': parsed_media[0]['source'],
                        'width': parsed_media[0]['width'],
                        'height': parsed_media[0]['height'],
                        'mimetype': 'image/jpeg',
                    }
                },
            },
        }

    def parse_byline(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.head'))
        items['byline'] = parsed_el.get('byline', '')

    def parse_news_identifier(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/Identification/NewsIdentifier'))
        items['guid'] = parsed_el['PublicIdentifier']
        items['version'] = parsed_el['RevisionId']
        # items['ingest_provider_sequence'] = parsed_el['ProviderId'] set by superdesk.io.ingest.IngestService.set_ingest_provider_sequence if None
        items['source_id'] = parsed_el['NewsItemId']  # for internal link lookup
        items['data'] = parsed_el['DateId']

    def parse_news_management(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsManagement'))
        if parsed_el.get('NewsItemType') != None:
            items['newsitemtype'] = parsed_el['NewsItemType']['FormalName']
        # if parsed_el.get('ThisRevisionCreated') != None:
        #     items['versioncreated'] = self.datetime(parsed_el['ThisRevisionCreated'])
        if parsed_el.get('FirstCreated') != None:
            items['firstcreated'] = self.datetime(parsed_el['FirstCreated'])
        if parsed_el.get('Status') != None:
            items['pubstatus'] = (parsed_el['Status']['FormalName']).lower()

    def parse_newslines(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsComponent/NewsLines'))
        items['headline'] = parsed_el.get('HeadLine', '')
        items['slugline'] = parsed_el.get('SlugLine', '')
        items['copyrightline'] = parsed_el.get('CopyrightLine', '')

    def parse_metadata(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsComponent/Metadata'))
        items['metadatatype'] = parsed_el['MetadataType']['FormalName']
        propertites = tree.findall('NewsItem/NewsComponent/Metadata/Property')
        sub = []

        for i in propertites:
            if i.get('FormalName', '') == 'DateLine':
                self.set_dateline(items, text=self.datetime(
                    i.get('Value', '')))  # TODO clarify format, maybe use also Location for city
            elif i.get('FormalName', '') == 'isPaidContent' and i.get('Value', '') == 'true':
                sub.append({
                    'name': 'paid content',
                    'parent': 'paid content',
                    'qcode': 'paid_content',
                    'scheme': 'paid_content',
                })

            elif i.get('FormalName', '') != '':
                items[(i.get('FormalName')).lower()] = i.get('Value', '')

        if len(sub) != 0:
            items['subject'] = sub

    def media_parser(self, tree):
        items = []
        for item in tree:
            if item.text is None:
                # read the attribute for the items
                if item.tag != 'HeadLine':
                    items.append(item.attrib)
        return items

    def parse_elements(self, tree):
        parsed = {}
        for item in tree:
            if item.text is None:
                # read the attribute for the items
                if item.tag != 'HeadLine':
                    parsed[item.tag] = item.attrib
            else:
                # read the value for the items
                parsed[item.tag] = item.text
        # remove empty objects
        parsed = {k: '' if not v else v for k, v in parsed.items()}
        return parsed

    def datetime(self, string):
        # Escenic datetime format from CE(S)T
        local_dt = datetime.datetime.strptime(string, '%Y%m%dT%H%M%S%z')
        return local_dt


register_feed_parser(EscenicXMLIFeedParser.NAME, EscenicXMLIFeedParser())
