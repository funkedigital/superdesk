import requests
from superdesk.io.feeding_services.rss import generate_tag_from_url

def import_images(associations, name, attributes):
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
