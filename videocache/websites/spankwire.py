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

VALIDATE_SPANKWIRE_DOMAIN_REGEX1 = re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.spankwire\.phncdn\.com')
VALIDATE_SPANKWIRE_DOMAIN_REGEX2 = re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.spankwire\.com')
VALIDATE_SPANKWIRE_VIDEO_EXT_REGEX = re.compile('(.*)\/(.*)\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)')

def check_spankwire_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'spankwire', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if (VALIDATE_SPANKWIRE_DOMAIN_REGEX1.search(host) or VALIDATE_SPANKWIRE_DOMAIN_REGEX2.search(host)) and VALIDATE_SPANKWIRE_VIDEO_EXT_REGEX.search(path):
        try:
            video_id = urllib.quote(path.strip('/').split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)

