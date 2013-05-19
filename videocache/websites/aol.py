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

VALIDATE_AOL_VIDEO_REGEX1 = re.compile('(.*)/[a-zA-Z0-9]+\/(.*)\.(flv|mp4)')
VALIDATE_AOL_VIDEO_REGEX2 = re.compile('(.*)/[0-9_]+\.(flv|mp4)')

def check_aol_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'aol', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if (host.find('videos.5min.com') > -1 or host.find('stream.aol.com') > -1) and (VALIDATE_AOL_VIDEO_REGEX1.search(path) or VALIDATE_AOL_VIDEO_REGEX2.search(path)):
        try:
            video_id = urllib.quote('_'.join(path.strip('/').split('/')[-2:]))
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

