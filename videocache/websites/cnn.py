#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re

def check_cnn_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'cnn', None, '', True, True

    if host.find('cdn.turner.com') > -1 and re.compile('(.*)/(.*)\.(flv)').search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

