#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re

def check_extremetube_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'extremetube', None, '', True, True

    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.extremetube\.phncdn\.com').search(host) and re.compile('(.*)\/[a-zA-Z0-9_-]+\.flv').search(path) and path.find('.flv') > -1:
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

