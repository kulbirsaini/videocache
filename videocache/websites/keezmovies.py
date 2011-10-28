#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re

def check_keezmovies_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'keezmovies', None, '', True, True

    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.keezmovies\.com').search(host) and re.compile('(.*)\/[0-9]+\.flv').search(path) and path.find('.flv') > -1:
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

