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

VALIDATE_WRZUTA_VIDEO_REGEX = re.compile('/(w[a-zA-Z0-9]+)/[a-zA-Z0-9]+$')

def check_wrzuta_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'wrzuta', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('c.wrzuta.pl') > -1 and VALIDATE_WRZUTA_VIDEO_REGEX.search(path):
        video_id = urllib.quote(VALIDATE_WRZUTA_VIDEO_REGEX.search(path).groups()[0]) + '.mp4'
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)

