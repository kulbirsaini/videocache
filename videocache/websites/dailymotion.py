#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re
import urlparse

def check_dailymotion_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'dailymotion', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('.dailymotion.com') > -1 and (re.compile('/video/[a-zA-Z0-9]{5,9}_?.*').search(path)):
        search = False
        try:
            video_id = re.compile('/video/([a-zA-Z0-9]{5,9})_?.*').search(path).group(1) + '.mp4'
        except Exception, e:
            pass
    elif (host.find('vid.akm.dailymotion.com') > -1 or re.compile('proxy[a-z0-9\-]?[a-z0-9]?[a-z0-9]?[a-z0-9]?\.dailymotion\.com').search(host)) and (path.find('.mp4') > -1 or path.find('.on2') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
        queue = False
        try:
            video_id = path.strip('/').split('/')[-1]
            video_id = video_id.replace('_hq.mp4', '.mp4')
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

