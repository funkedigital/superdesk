import json
import os
from superdesk.tests import TestCase
from apps.publish import init_app
from fd.publish.formatters.fd_ninjs_formatter import FDNINJSFormatter
import fd.publish.formatters.fd_data_layer
from copy import deepcopy


class FDNINJSFormatterTest(TestCase):
    base_article = {
        "_id": "urn:newsml:localhost:2020-05-13T09:24:45.989740:449dd919-bafa-4f0d-a55c-93cc9a0fd1c9",
        "family_id": "urn:newsml:localhost:2020-05-13T09:24:45.989740:449dd919-bafa-4f0d-a55c-93cc9a0fd1c9",
        "guid": "urn:newsml:localhost:2020-05-13T09:24:45.989740:449dd919-bafa-4f0d-a55c-93cc9a0fd1c9",
        "headline": "test article",
        "priority": 6,
        "type": "text",
        "place": [],
        "urgency": 3,
        "_etag": "bae74e989bf59371e87bbc6374c89f193cc50944",
        "schedule_settings": {
            "utc_publish_schedule": None,
            "utc_embargo": None,
            "time_zone": None
        },
        "sign_off": "ADM",
        "pubstatus": "usable",
        "event_id": "tag:localhost:2020:ba81b62b-9e1a-4386-be5e-4a7269ec43fe",
        "source": "wmn",
        "profile": "5d48392332827c0ea7f5e5a6",
        "subject": [
            {
                "qcode": "advertising",
                "parent": "advertising",
                "name": "advertising",
                "scheme": "seo_metadata"
            }
        ],
        "version": 1,
        "_current_version": 2,
        "format": "HTML",
        "genre": [
            {
                "qcode": "Article",
                "name": "Article (news)"
            }
        ],
        "expiry": None,
        "task": {
            "stage": "5d0b88d910e7ed66382aa4a4",
            "user": "5cd959635b7d107ad01d7ff5",
            "desk": "5d0b88d910e7ed66382aa4a6"
        },
        "version_creator": "5cd959635b7d107ad01d7ff5",
        "state": "published",
        "operation": "publish",
        "unique_name": "#3907",
        "template": "5ebaeeb72c59a95ed751ee16",
        "language": "en",
        "original_creator": "5cd959635b7d107ad01d7ff5",
        "body_html": "<p>test article</p>",
        "flags": {
            "marked_for_legal": False,
            "marked_archived_only": False,
            "marked_for_sms": False,
            "marked_for_not_publication": False
        },
        "unique_id": 3907,
        "lock_action": None,
        "lock_session": None,
        "lock_time": None,
        "lock_user": None,
        "abstract": "<p>test article</p>",
        "annotations": [],
        "associations": {},
        "authors": [
            {
                "scheme": None,
                "role": "writer",
                "name": "Autor",
                "parent": "5cd959635b7d107ad01d7ff5",
                "_id": [
                    "5cd959635b7d107ad01d7ff5",
                    "writer"
                ],
                "sub_label": "Admin Istrator"
            }
        ],
        "extra": {
            "seo_description": "<p>test article</p>",
            "seo_title": "test article"
        },
        "fields_meta": {
            "headline": {
                "draftjsState": [
                    {
                        "entityMap": {},
                        "blocks": [
                            {
                                "key": "cpgv5",
                                "data": {
                                    "MULTIPLE_HIGHLIGHTS": {}
                                },
                                "depth": 0,
                                "type": "unstyled",
                                "entityRanges": [],
                                "inlineStyleRanges": [],
                                "text": "test article"
                            }
                        ]
                    }
                ]
            },
            "abstract": {
                "draftjsState": [
                    {
                        "entityMap": {},
                        "blocks": [
                            {
                                "key": "t1ta",
                                "data": {
                                    "MULTIPLE_HIGHLIGHTS": {}
                                },
                                "depth": 0,
                                "type": "unstyled",
                                "entityRanges": [],
                                "inlineStyleRanges": [],
                                "text": "test article"
                            }
                        ]
                    }
                ]
            },
            "extra>seo_description": {
                "draftjsState": [
                    {
                        "entityMap": {},
                        "blocks": [
                            {
                                "key": "4tuur",
                                "data": {
                                    "MULTIPLE_HIGHLIGHTS": {}
                                },
                                "depth": 0,
                                "type": "unstyled",
                                "entityRanges": [],
                                "inlineStyleRanges": [],
                                "text": "test article"
                            }
                        ]
                    }
                ]
            },
            "body_html": {
                "draftjsState": [
                    {
                        "entityMap": {},
                        "blocks": [
                            {
                                "key": "1kmv9",
                                "data": {
                                    "MULTIPLE_HIGHLIGHTS": {}
                                },
                                "depth": 0,
                                "type": "unstyled",
                                "entityRanges": [],
                                "inlineStyleRanges": [],
                                "text": "test article"
                            }
                        ]
                    }
                ]
            },
            "extra>seo_title": {
                "draftjsState": [
                    {
                        "entityMap": {},
                        "blocks": [
                            {
                                "key": "ds9ok",
                                "data": {
                                    "MULTIPLE_HIGHLIGHTS": {}
                                },
                                "depth": 0,
                                "type": "unstyled",
                                "entityRanges": [],
                                "inlineStyleRanges": [],
                                "text": "test article"
                            }
                        ]
                    }
                ]
            }
        },
        "keywords": [
            "test article"
        ],
        "slugline": "test article",
        "word_count": 2,
        "publish_schedule": None,
        "force_unlock": True
    }

    def setUp(self):
        self.formatter = FDNINJSFormatter()
        init_app(self.app)
        self.maxDiff = None

    def test_fd_ninjs_formatter(self):
        article = deepcopy(self.base_article)

        seq, doc = self.formatter.format(article, {'_id': 1, 'name': 'Test formatter'})[0]
        expected = {
            "extra": {
                "seo_description": "<p>test article</p>",
                "seo_title": "test article",
                "advertising": True,
                'uniqueName': '3907'
            },
            "language": "en",
            "annotations": [],
            "urgency": 3,
            "slugline": "test article",
            "charcount": 12,
            "source": "wmn",
            "keywords": [
                "test article"
            ],
            "body_html": "<p>test article</p>",
            "genre": [
                {
                    "code": "Article",
                    "name": "Article (news)"
                }
            ],
            "wordcount": 2,
            "headline": "test article",
            "authors": [
                {
                    "code": "Autor",
                    "name": "Autor",
                    "role": "writer",
                    "biography": ""
                }
            ],
            "subject": [
                {
                    "code": "advertising",
                    "scheme": "seo_metadata",
                    "name": "advertising"
                }
            ],
            "readtime": 0,
            "priority": 6,
            "profile": "5d48392332827c0ea7f5e5a6",
            "type": "text",
            "version": "2",
            "description_text": "test article",
            "description_html": "<p>test article</p>",
            "guid": "urn:newsml:localhost:2020-05-13T09:24:45.989740:449dd919-bafa-4f0d-a55c-93cc9a0fd1c9",
            "pubstatus": "usable",
            "products": []
        }
        self.assertEqual(expected, json.loads(doc))

    def test_subject_to_extra_formatter(self):
        article = deepcopy(self.base_article)

        article.get('subject', []).append(
            {
                "qcode": "no_index",
                "parent": "no index",
                "name": "no index / no follow",
                "scheme": "seo_metadata"
            }
        )

        article.get('subject', []).append(
            {
                "qcode": "allow_comments",
                "parent": "allow comments",
                "name": "allow comments",
                "scheme": "seo_metadata"
            }
        )

        article.get('subject', []).append(
            {
                "qcode": "republish",
                "parent": "republish",
                "name": "republish",
                "scheme": "seo_metadata"
            }
        )

        seq, doc = self.formatter.format(article, {'_id': 1, 'name': 'Test extra'})[0]
        expected = {
            "extra": {
                "seo_description": "<p>test article</p>",
                "seo_title": "test article",
                "advertising": True,
                "no_index": True,
                "allow_comments": True,
                "republish": True,
                'uniqueName': '3907'
            }
        }

        self.assertEqual(expected.get('extra'), json.loads(doc).get('extra'))

    def test_seo_metadata_advertising(self):
        article = deepcopy(self.base_article)

        seq, doc = self.formatter.format(article, {'_id': 1, 'name': 'Test extra'})[0]
        expected = {
            "extra": {
                "seo_description": "<p>test article</p>",
                "seo_title": "test article",
                "advertising": True,
                'uniqueName': '3907'
            }
        }

        self.assertEqual(expected.get('extra'), json.loads(doc).get('extra'))

    def test_seo_metadata_no_index(self):
        article = deepcopy(self.base_article)

        article.get('subject', []).append(
            {
                "qcode": "no_index",
                "parent": "no index",
                "name": "no index / no follow",
                "scheme": "seo_metadata"
            }
        )

        seq, doc = self.formatter.format(article, {'_id': 1, 'name': 'Test extra'})[0]

        expected = {
            "extra": {
                "seo_description": "<p>test article</p>",
                "seo_title": "test article",
                "no_index": True,
                "advertising": True,
                'uniqueName': '3907'
            }
        }

        self.assertEqual(expected.get('extra'), json.loads(doc).get('extra'))

    def test_seo_metadata_allow_comments(self):
        article = deepcopy(self.base_article)

        article.get('subject', []).append(
            {
                "qcode": "allow_comments",
                "parent": "allow comments",
                "name": "allow comments",
                "scheme": "seo_metadata"
            }
        )

        seq, doc = self.formatter.format(article, {'_id': 1, 'name': 'Test extra'})[0]

        expected = {
            "extra": {
                "seo_description": "<p>test article</p>",
                "seo_title": "test article",
                "allow_comments": True,
                "advertising": True,
                'uniqueName': '3907'
            }
        }

        self.assertEqual(expected.get('extra'), json.loads(doc).get('extra'))

    def test_seo_metadata_republish(self):
        pass


