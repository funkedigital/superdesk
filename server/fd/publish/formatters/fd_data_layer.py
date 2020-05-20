import logging
import re

from superdesk import get_resource_service, app

logger = logging.getLogger(__name__)


def get_content_type(article):
    """Get content type"""

    try:
        profile = article['profile']
    except KeyError:
        logger.warning("missing profile in article (guid: {guid})".format(guid=article.get("guid")))
        return ""
    else:
        content_profile = get_resource_service("content_types").find_one(
            _id=profile, req=None)
        if content_profile:
            content_type = ''
            if content_profile['label']:
                for c in content_profile['label'].split('_'):
                    content_type += c[0]
            return content_type
        else:
            return ""


def count_internal_links(data_layer, body):
    """Get the articles internal links"""

    internal_urls = re.findall('<a\s+href=["\']urn:newsml:([^"\']+)["\']',
                               body)
    if internal_urls:
        data_layer['internalLink'] = True
        data_layer['InternalLinksCount'] = len(internal_urls)
    else:
        data_layer['internalLink'] = False
        data_layer['InternalLinksCount'] = 0


def articles_correction_count(data_layer, family_id, base_headline):
    """Get the articles correction count"""

    item = list(
        get_resource_service('archive_history').get(req=None, lookup={
            'item_id': family_id, 'operation': 'correct'}))
    # if first published version
    if len(item) == 0:
        data_layer['correctionCount'] = 0
        data_layer['pageRepublished'] = False
    else:
        if len(item) == 1:
            data_layer['previousTitle'] = base_headline
            data_layer['correctionCount'] = 1
            data_layer['pageRepublished'] = True
        else:
            logger.info(item[-2]['update']['headline'])
            data_layer['previousTitle'] = item[-2]['update']['headline']
            data_layer['pageRepublished'] = True
            data_layer['correctionCount'] = len(item)


def get_data_layer(article):
    """Get the data layer infos"""

    data_layer = {}
    if article:
        # add content type
        content_type = get_content_type(article)
        if content_type:
            data_layer['contentType'] = content_type

            # TODO - add word count
            data_layer['wordcount'] = 0

            # add internal links count
            if article.get('body_html'):
                count_internal_links(data_layer, article.get('body_html'))
            # if article has been corrected deliver the corrections count and previous title
            if article.get('family_id') and article.get('headline'):
                articles_correction_count(data_layer, article.get('family_id'), article.get('headline'))

    return data_layer
