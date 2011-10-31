#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urlparse

def check_aol_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'aol', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('stream.aol.com') > -1 and re.compile('(.*)/[a-zA-Z0-9]+\/(.*)\.(flv)').search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
        try:
            video_id = '_'.join(path.strip('/').split('/')[-2:])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

