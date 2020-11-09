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
import html
import requests
import re
import superdesk

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


class SpotonFeedParser(XMLFeedParser):
    """ Feed Parser for SpotOn """

    NAME = 'spoton'
    NSPS = {'schemaLocation': 'http://schema.spot-on-news.de'}

    label = 'SpotOn Parser'

    def can_parse(self, xml):
        return xml.tag == 'NewsML'

    def parse(self, xml, provider=None):
        items = {'associations': {}}
         
        try:
            self.parse_metadata(items, xml)
            self.parse_content(items, xml)
            self.parse_teaser(items, xml)
            return items
        except Exception as ex:
            logger.info(ex)
    
    def parse_metadata(self, items, xml):
        items['extra'] = {}
        meta_elements = self.parse_elements(xml.find('schemaLocation:Meta', namespaces=self.NSPS))

        author = [{
                    'name':  meta_elements.get('Author', ''),
                    'role': 'writer',
                    'avatar_url': 'https://api.adorable.io/avatars/285/abott@adorable.png'
            }]
        items['authors'] = author

        content_validity_elem = meta_elements.get('ValidTo', '')
        items['extra'].update( {'content_validity' : content_validity_elem} )
        
        if meta_elements.get('Revision') != None:
            items['version'] = int(meta_elements.get('Revision'))

        if meta_elements.get('URN') != None:
            items['uri'] = meta_elements.get('URN')

        if meta_elements.get('Priority') != None:
            items['priority'] = int(meta_elements.get('Priority'))

        items['format'] = meta_elements.get('Format', 'html')

        keywords_elem = xml.find('schemaLocation:Meta/schemaLocation:Keywords', namespaces=self.NSPS)
        keywords = []
        if len(keywords_elem) > 0:
            for k in keywords_elem:
                keywords.append(k.text)
        items['keywords'] = keywords

        revision_created = meta_elements.get('RevisionCreated', '')
        if len(revision_created) > 0:
            items['versioncreated'] = self.datetime(revision_created)
        
        first_created = meta_elements.get('FirstCreated', '')
        if len(first_created) > 0:
            items['firstcreated'] = self.datetime(first_created)  
        
        location = meta_elements.get('Location', '')
        items['extra'].update( {'location' : location} )
        
        department = meta_elements.get('Department', '')
        items['extra'].update( {'department' : department} )

        headline_elem = xml.find('schemaLocation:Content/schemaLocation:Headline', namespaces=self.NSPS)
        items['headline'] = headline_elem.text
        items['extra'].update( {'seo_title' : headline_elem.text} )


        slugline = re.sub('[^A-zZüÜäÄöÖßaé0-9]+', ' ', headline_elem.text)
        slugline = ' '.join(slugline.split())
        slugline = slugline.lower().replace(' ', '-')

        items['slugline'] = slugline

        items['guid'] = xml.find('schemaLocation:Meta/schemaLocation:URN', namespaces=self.NSPS).text


    def parse_content(self, items, xml):

        body = xml.find('schemaLocation:Content/schemaLocation:Body/schemaLocation:Pages', namespaces=self.NSPS)
        body_html = ''
        for action, el in etree.iterwalk(body):
            elem_tag = el.tag.replace('{' + self.NSPS.get('schemaLocation') + '}', '')
            if elem_tag == 'Text':
                if el.text.find('<script') != -1:
                    continue
                elif el.text.find('spotonTrackOutboundLink') != -1:
                    text_block = el.text.replace('onclick="spotonTrackOutboundLink(this.href)"', '')
                    body_html += html.unescape(text_block.encode().decode("utf-8"))
                else:
                    body_html += html.unescape(el.text.encode().decode("utf-8"))

        items['body_html'] = body_html
    
    
    def parse_teaser(self, items, xml):

        attributes = {}
        
        teaser_description_elem = xml.find('schemaLocation:Content/schemaLocation:Teaser/schemaLocation:Text', namespaces=self.NSPS)
        attributes['description'] = teaser_description_elem.text

        teaser_media_elem = xml.find('schemaLocation:Content/schemaLocation:Teaser/schemaLocation:Media/schemaLocation:Image', namespaces=self.NSPS)
        attributes['source'] = teaser_media_elem.get('src')
        attributes['width'] = teaser_media_elem.get('width')
        attributes['height'] = teaser_media_elem.get('height')

        teaser_caption_elem = xml.find('schemaLocation:Content/schemaLocation:Teaser/schemaLocation:Media/schemaLocation:Image/schemaLocation:Caption', namespaces=self.NSPS)
        attributes['caption'] = teaser_caption_elem.text

        teaser_copyright_elem = xml.find('schemaLocation:Content/schemaLocation:Teaser/schemaLocation:Media/schemaLocation:Image/schemaLocation:Copyright', namespaces=self.NSPS)
        attributes['copyright'] = teaser_copyright_elem.text

        self.import_images(items['associations'], 'featuremedia', attributes)

    def import_images(self, associations, name, attributes):
        """ import images to mongo """
        href = attributes.get('source', '')
        sc = requests.get(href)

        if sc.status_code == 200:
            description = attributes.get('description', 'picture description')
            if len(description) == 0:
                description = 'picture description'
                
            associations[name] = {
                'type': 'picture',
                'guid': generate_tag_from_url(
                    attributes.get('source', '')),
                'pubstatus': 'usable',
                'headline': attributes.get('headline', 'picture'),
                'alt_text': attributes.get('caption', 'alt text'),
                'creditline': attributes.get('copyright', 'picture'),
                'description_text': description,
                'mimetype': 'image/jpeg',
                'renditions': {
                    'baseImage': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                    },
                    'viewImage': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                    },
                    'thumbnail': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                    },
                    'original': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                    }
                },
            }

    def parse_elements(self, tree):
        parsed = {}
        for item in tree:
            # read the value for the items
            parsed[item.tag.replace('{' + self.NSPS.get('schemaLocation') + '}', '')] = item.text
        # remove empty objects
        parsed = {k: '' if not v else v for k, v in parsed.items()}
        return parsed

    def datetime(self, string):
        # Escenic datetime format from CE(S)T
        local_dt = datetime.datetime.strptime(string, '%a, %d %b %Y %H:%M:%S %z')
        return local_dt

register_feed_parser(SpotonFeedParser.NAME, SpotonFeedParser())