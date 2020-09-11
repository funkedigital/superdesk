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
        items = {'associations': {}}
         
        try:

            self.parse_newslines(items, xml)
            self.parse_feature_media(items, xml)
            self.parse_news_identifier(items, xml)
            self.parse_metadata(items, xml)
            self.parse_byline(items, xml)
            self.parse_slugline(items, xml)
            self.parse_abstract(items, xml)
            self.parse_news_management(items, xml)
            self.parse_body_html(items, xml)

            return items
        except Exception as ex:
            raise ParserError.newsmlTwoParserError(ex, provider)

    def import_images(self, associations, name, attributes):
        """ import images to mongo """
        href = attributes.get('source', '')
        sc = requests.get(href)

        if sc.status_code == 200:
            description = attributes.get('alternate-text', 'picture description')
            if len(description) == 0:
                description = 'picture description'
                
            associations[name] = {
                'type': 'picture',
                'guid': generate_tag_from_url(
                    attributes.get('source', '')),
                'headline': attributes.get('headline', 'picture'),
                'alt_text': attributes.get('alt-text', 'alt text'),
                'creditline': attributes.get('copyright', 'picture'),
                'description_text': description,
                'mimetype': 'image/jpeg',
                'renditions': {
                    'baseImage': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                        "CropTop": 0
                    },
                    'viewImage': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                        "CropTop": 0
                    },
                    'thumbnail': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                        "CropTop": 0
                    },
                    'original': {
                        'href': href,
                        'width': attributes.get('width', ''),
                        'height': attributes.get('height', ''),
                        'mimetype': 'image/jpeg',
                        "CropTop": 0
                    }
                },
            }

    def import_gallery(self, elem, name, associations):
        """ import the media gallery """
        # process inline images
        atts = {}
        counter = 0
        if elem.get('class') == 'body' and ( elem.get('media-type') == 'image' or elem.get('media-type') == 'gallery'):
            for action, x in etree.iterwalk(elem):
                if x.tag == 'media-reference':
                        counter +=1
                        sc = requests.get(x.get('source'))
                        if sc.status_code == 200:
                            atts['source'] = x.get('source')
                            atts['width'] = x.get('width')
                            atts['height'] = x.get('height')
                            atts['alt-text'] = x.get('alternate-text', 'alt')
                            atts['copyright'] = x.get('copyright', 'copyright')

                if x.tag == 'media-caption':
                    if len(atts) > 0:
                        atts['media-caption'] = x.text
                
                if len(atts) > 0:
                    self.import_images(associations, name + str(counter), atts)


    def import_media_tag(self, name, elem, associations, counter):
        """ import the media tags """
        # process inline images
        atts = {}
        if elem.get('class') == 'body' and elem.get('media-type') == 'image':
            for action, x in etree.iterwalk(elem):
                if x.get('width') and len(x.get('source')) > 0:
                    if x.tag == 'media-reference':
                        sc = requests.get(x.get('source'))
                        if sc.status_code == 200:
                            atts['source'] = x.get('source')
                            atts['width'] = x.get('width')
                            atts['height'] = x.get('height')
                            atts['alt-text'] = x.get('alternate-text', 'alt')
                            atts['copyright'] = x.get('copyright', 'copyright')
                if x.tag == 'media-caption':
                    if len(atts) > 0:
                        atts['media-caption'] = x.text
            if len(atts) > 0:
                self.import_images(associations, 'editor_' + str(counter), atts)
                return '<p>&nbsp;</p><!-- EMBED START Image {id: "editor_'+str(counter)+'"} --><figure>    <img src="' + atts.get('source') + '" alt="' + atts.get('media-caption', '') + '" />    <figcaption>' + atts.get('media-caption', '') + '</figcaption></figure><!-- EMBED END Image {id: "editor_'+ str(counter) +'"} --><p>&nbsp;</p>'             
            else: 
                return ""
        else:
            return ""
         

    def parse_media(self, items, xml):
        root = lxml.html.fromstring(xml)
        inline_img = 0
        for action, el in etree.iterwalk(root):
            # process inline images and remove them from the tree
            if el.tag == 'media' and el.get('media-type') == 'image' and el.get('class') == 'body':
                for br in el.xpath('.'):
                    inline_img += 1
                    elem = self.import_media_tag('editor_', br, items['associations'], inline_img)
                    br.tail = elem + br.tail
                    br.drop_tree()
            if el.tag == 'media' and el.get('media-type') == 'gallery' and el.get('class') == 'body':
                for br in el.xpath('.'):
                    self.import_gallery(br, 'gallery--', items['associations'])
                    #br.tail = elem + br.tail
                    br.drop_tree()
            if el.tag == 'media' and el.get('class') == 'teaser':
                for br in el.xpath('.'):
                    br.drop_tree()
        return etree.tostring(root)

    def parse_body_html(self, items, tree):
        """ parses the elements of the body """

        body_xml = etree.tostring(
            tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.content'),
            encoding='unicode').replace('<body.content>', '').replace('</body.content>', '')

        # transform the media elements
        body_xml = self.parse_media(items, body_xml)
        body_html = html.unescape(body_xml.decode("utf-8"))
        #remove spaces betwen tags
        body_html = re.sub(">\s*<","><",body_html)
        # remove p tags after media
        body_html = body_html.replace('</media></p>', '</media>')
        # add p tag before the media to wrap the title
        body_html = body_html.replace('<media class', '</p><media class')
        body_html= body_html.replace('alternate-text', 'data-alternate-text')
        body_html = body_html.replace('hl2', 'h2')
        body_html = body_html.replace('hl3', 'h2')
        body_html = body_html.replace('hl4', 'h2')
        body_html = body_html.replace('hl5', 'h2')
        body_html = body_html.replace('hl6', 'h2')
        body_html = re.sub("<[^>/][^>]*></[^>]*>","",body_html)
        body_html = re.sub("<[^>/][^>]*>&nbsp;</[^>]*>","",body_html)

        items['body_html'] = body_html
       
        items['pubstatus'] = 'usable'

    def parse_feature_media(self, items, tree):
        parsed_media = self.media_parser(
            tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.content/media'))
        try:
            feature_media = parsed_media[0]

            for media in parsed_media:
                if int(media['width']) > int(feature_media['width']):
                    feature_media = media
            try:
                feature_media = [feature_media]
                if bool(feature_media[0]):
                    self.import_images(items['associations'], 'featuremedia', feature_media[0])
            except IndexError:
                pass
        except Exception as e:
            logger.info(e)


    def parse_byline(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.head'))
        items['byline'] = parsed_el.get('byline', 'byline default')

    def parse_abstract(self, items, tree):
        parsed_el = tree.findall('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.head/hedline/hl2')
        for x in parsed_el:
            if x.get('class') == 'deck':
                items['abstract'] = x.text

    def parse_slugline(self, items, tree):
        parsed_el = tree.findall('NewsItem/NewsComponent/Metadata/Property')
        for x in parsed_el:
            if x.get('FormalName', '') == 'URL':
                slug = x.get('Value', '').split("/")[-1].rsplit('.', 1)[0]
                items['slugline'] = slug
                items['unique_name'] = '#' + slug.split("-id")[-1] 
                items['unique_id'] = int(slug.split("-id")[-1])

    def parse_news_identifier(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/Identification/NewsIdentifier'))
        items['guid'] = parsed_el['PublicIdentifier']
        items['version'] = parsed_el['RevisionId']
        items['source_id'] = parsed_el['NewsItemId']  # for internal link lookup
        items['data'] = parsed_el['DateId']

    def parse_news_management(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsManagement'))
        if parsed_el.get('NewsItemType') != None:
            items['newsitemtype'] = parsed_el['NewsItemType']['FormalName']
        if parsed_el.get('FirstCreated') != None:
            items['firstcreated'] = self.datetime(parsed_el['FirstCreated'])

    def parse_newslines(self, items, tree):
        parsed_el = self.parse_elements(tree.find('NewsItem/NewsComponent/NewsLines'))
        items['headline'] = parsed_el.get('HeadLine', 'picture')
        items['slugline'] = parsed_el.get('HeadLine', 'picture')
        items['copyrightline'] = parsed_el.get('CopyrightLine', 'picture')

    def parse_metadata(self, items, tree):
        items['extra'] = {}
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

            elif i.get('FormalName', '') == 'Channel':
                items['extra'].update( {'waz_channel' : i.get('Value', '')} )
           
            elif i.get('FormalName', '') == 'Author':
                author = [{
                    #'uri': None,
                    #'parent': None,
                    'name': i.get('Value', ''),
                    'role': 'writer',
                    #'jobtitle': None,
                    'avatar_url': 'https://api.adorable.io/avatars/285/abott@adorable.png'
                }]

                items['authors'] = author

            elif i.get('FormalName', '') == 'SeoHeadline':
                items['extra'].update( {'seo_title' : i.get('Value', '')} )

            elif i.get('FormalName', '') != '':
                items[(i.get('FormalName')).lower()] = i.get('Value', '')
        
        parsed_el = tree.findall('NewsItem/NewsComponent/ContentItem/DataContent/nitf/body/body.head/hedline/hl2')
        for x in parsed_el:
            if x.get('class') == 'kicker' and x.text:
                items['extra'].update( {'kicker' : x.text} )

        if len(sub) != 0:
            items['subject'] = sub

    def media_parser(self, tree):
        items = []
        if tree is not None:
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
