#!/usr/bin/env python
#
# (C) Copyright 2008-2011 White Magnet Software Private Limited
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import re

def check_breakcom_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'breakcom', None, '', True, True

    if host.find('.break.com') > -1 and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
        try:
            video_id = path.strip('/').split('/')[-1]
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

