#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import cgi
import re
import urllib
import urlparse

def check_megavideo_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'megavideo', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('megavideo.com') > -1:
        try:
            dict = cgi.parse_qs(query)
            video_id = urllib.quote(dict.get('v', ''))
            if video_id == '': video_id = None
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

