#!/usr/bin/env python
#
# (C) Copyright Kulbir Saini <saini@saini.co.in>
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urllib
import urlparse

VALIDATE_XVIDEOS_VIDEO_REGEX = re.compile('videos\/flv\/(.*)\/(.*)\.(flv|mp4)')

def check_xvideos_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'xvideos', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('.xvideos.com') > -1 and VALIDATE_XVIDEOS_VIDEO_REGEX.search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
        try:
            video_id = urllib.quote(path.strip('/').split('/')[-1].split('_')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)

