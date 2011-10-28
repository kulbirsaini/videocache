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

def check_megavideo_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'megavideo', None, '', True, True

    if host.find('megavideo.com') > -1:
        try:
            dict = cgi.parse_qs(query)
            video_id = dict.get('v', None)
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

