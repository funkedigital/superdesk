import html
import logging

from fd.publish.formatters.fd_data_layer import get_data_layer
from superdesk.publish.formatters.ninjs_newsroom_formatter import NewsroomNinjsFormatter
from superdesk.metadata.item import FORMATS, FORMAT, GUID_FIELD, FAMILY_ID

logger = logging.getLogger(__name__)


class FDNINJSFormatter(NewsroomNinjsFormatter):

    def __init__(self):
        self.format_type = 'fd ninjs'
        self.can_preview = False
        self.can_export = False
        self.internal_renditions = ['original', 'viewImage', 'baseImage']

    def _transform_to_ninjs(self, article, subscriber, recursive=True):
        ninjs = super()._transform_to_ninjs(article, subscriber, recursive)
        logger.info('formatting the ninjs')
        
        if 'extra' in ninjs:
            if 'subject' in ninjs:
                subjects = article.get('subject', [])
                for x in subjects:
                    option = x.get('qcode')
                    if option:
                        ninjs['extra'][option] = True
                    
            if article.get('unique_name'):
                ninjs['extra']['uniqueName'] = article.get('unique_name').replace('#', '')

        # if article.get('body_html'):
        #     # get the data layer infos
        #     data_layer = get_data_layer(article)
        #     if data_layer:
        #         ninjs['extra']['dataLayer'] = data_layer

        return ninjs
