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

VALIDATE_METACAFE_DOMAIN_REGEX = re.compile('\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)')

def check_metacafe_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'metacafe', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if (host.find('.mccont.com') > -1 or host.find('akvideos.metacafe.com') > -1 ) and path.find('ItemFiles') > -1 and VALIDATE_METACAFE_DOMAIN_REGEX.search(path):
        try:
            video_id = urllib.quote(urllib.unquote(path).strip('/').split(' ')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)

