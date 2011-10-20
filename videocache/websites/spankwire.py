#!/usr/bin/env python
#
# (C) Copyright 2008-2011 White Magnet Software Private Limited
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re

def check_spankwire_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'spankwire', None, '', True, True

    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.spankwire\.com').search(host) and re.compile('(.*)\/(.*)\.flv').search(path) and path.find('.flv') > -1:
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

