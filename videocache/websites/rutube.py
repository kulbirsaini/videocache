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

VALIDATE_RUTUBE_VIDEO_REGEX = re.compile('video(.*)\.rutube\.ru\/(.*)/([a-zA-Z0-9.]+)\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)Seg[0-9]+-Frag[0-9]+')

def check_rutube_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'rutube', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('.rutube.ru') > -1 and VALIDATE_RUTUBE_VIDEO_REGEX.search(url):
        try:
            video_id = urllib.quote(path.strip('/').split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)
