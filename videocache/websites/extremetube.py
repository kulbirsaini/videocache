#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urllib2
import urlparse

def check_extremetube_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'extremetube', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.extremetube\.phncdn\.com').search(host) and re.compile('(.*)\/[a-zA-Z0-9_-]+\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)').search(path):
        try:
            video_id = urllib2.quote(path.strip('/').split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

