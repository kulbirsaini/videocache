#!/usr/bin/env python
#
# (C) Copyright 2008-2011 White Magnet Software Private Limited
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re

def check_myspace_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'myspace', None, '', True, True

    if (re.compile('(.*)\.myspacecdn\.com').search(host) or re.compile('(.*)\.myspacecdn\.(.*)\.footprint\.net').search(host)) and re.compile('(.*)\/[a-zA-Z0-9]+\/vid\.mp4').search(path) and path.find('.mp4') > -1:
        try:
            video_id = path.strip('/').split('/')[-2] + '.mp4'
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

