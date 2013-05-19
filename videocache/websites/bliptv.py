#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urllib
import urlparse

VALIDATE_BLIPTV_DOMAIN_REGEX = re.compile('\.video[a-z0-9]?[a-z0-9]?[a-z0-9]?\.blip\.tv')
VALIDATE_BLIPTV_VIDEO_EXT_REGEX = re.compile('\.(mp4|flv|mov|mkv|avi|rm|rmvb|mp3|m4v|wmv|mpg|mpeg|3gp)')

def check_bliptv_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'bliptv', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if path.find('filename=') < 0 and VALIDATE_BLIPTV_DOMAIN_REGEX.search(host) and VALIDATE_BLIPTV_VIDEO_EXT_REGEX.search(path):
        try:
            video_id = urllib.quote(path.strip('/').split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

