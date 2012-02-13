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
import urlparse

def check_weather_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'weather', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('v.imwx.com') > -1 and re.compile('v\/wxcom\/[a-zA-Z0-9]+\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)').search(path) and re.compile('videoId=[0-9]+&').search(query):
        try:
            dict = cgi.parse_qs(query)
            video_id = dict['videoId'][0]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

