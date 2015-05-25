#!/usr/bin/env python
#
# (C) Copyright Kulbir Saini <saini@saini.co.in>
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urlparse

VALIDATE_VIMEO_VIDEO_EXT_REGEX = re.compile('\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg)')

def check_vube_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'vube', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('video.thestaticvube.com') > -1 and VALIDATE_VIMEO_VIDEO_EXT_REGEX.search(path):
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue, report_hit)

