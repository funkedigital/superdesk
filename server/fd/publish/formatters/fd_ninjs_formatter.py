import html
import logging
import re

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
        if 'extra' in ninjs:
            if 'subject' in ninjs:
                subjects = article.get('subject', [])
                for x in subjects:
                    option = x.get('qcode')
                    if option:
                        ninjs['extra'][option] = True
            if 'slugline' in ninjs:
                slugline = article.get('slugline')
                if not slugline[-1].isdigit():
                    unique_name = article.get('unique_name').replace('#', '')
                    ninjs['slugline'] = slugline + '-id' + str(unique_name)

        return ninjs
