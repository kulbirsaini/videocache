#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os
import re
import urllib
import urlparse

def check_dailymotion_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'dailymotion', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('.dailymotion.com') > -1 and (re.compile('^/video/[a-zA-Z0-9]{5,9}_?.*').search(path)):
        search = False
        try:
            video_id = urllib.quote(re.compile('/video/([a-zA-Z0-9]{5,9})_?.*').search(path).group(1))
        except Exception, e:
            pass
    elif (host.find('vid.ec.dmcdn.net') > -1 or host.find('vid.akm.dailymotion.com') > -1 or re.compile('proxy[a-z0-9\-]?[a-z0-9]?[a-z0-9]?[a-z0-9]?\.dailymotion\.com').search(host)) and re.compile('\.(flv|mp4|avi|mkv|mp3|rm|rmvb|m4v|mov|wmv|3gp|mpg|mpeg|on2)').search(path):
        queue = False
        try:
            video_id = '.'.join(urllib.quote(path.strip('/').split('/')[-1]).split('.')[:-1])
            video_id = video_id.replace('_hq', '')
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

