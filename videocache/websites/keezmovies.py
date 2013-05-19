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

VALIDATE_KEEZMOVIES_DOMAIN_REGEX1 = re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.keezmovies\.com')
VALIDATE_KEEZMOVIES_DOMAIN_REGEX2 = re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.keezmovies\.phncdn\.com')
VALIDATE_KEEZMOVIES_VIDEO_EXT_REGEX = re.compile('(.*)\/[0-9a-zA-Z_\-]+\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)')

def check_keezmovies_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'keezmovies', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if (VALIDATE_KEEZMOVIES_DOMAIN_REGEX1.search(host) or VALIDATE_KEEZMOVIES_DOMAIN_REGEX2.search(host)) and VALIDATE_KEEZMOVIES_VIDEO_EXT_REGEX.search(path):
        try:
            video_id = urllib.quote(path.strip('/').split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

