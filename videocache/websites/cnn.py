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

VALIDATE_CNN_DOMAIN_REGEX = re.compile('cnn-[a-zA-Z0-9]?[a-zA-Z0-9]?[a-zA-Z0-9]?\.akamaihd\.net')
VALIDATE_CNN_VIDEO_EXT_REGEX = re.compile('cnn\/.*_([0-9]+)_.*\.(mp4|flv).*bitrate=([0-9]+)')

def check_cnn_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'cnn', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if VALIDATE_CNN_DOMAIN_REGEX.search(host) and VALIDATE_CNN_VIDEO_EXT_REGEX.search(path):
        try:
            match = VALIDATE_CNN_VIDEO_EXT_REGEX.search(path).groups()
            video_id = urllib.quote(match[0] + '_' + match[2] + '.' + match[1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

