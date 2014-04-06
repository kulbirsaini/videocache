#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import cgi
import re
import urllib
import urlparse

VALIDATE_WEATHER_VIDEO_REGEX = re.compile('v\/wxcom\/[a-zA-Z0-9_]+\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)')
VALIDATE_WEATHER_ARG_REGEX = re.compile('videoId=[0-9]+&')

def check_weather_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'weather', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('v.imwx.com') > -1 and VALIDATE_WEATHER_VIDEO_REGEX.search(path) and VALIDATE_WEATHER_ARG_REGEX.search(query):
        try:
            video_id = urllib.quote(path.strip().split('/')[-1])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)

