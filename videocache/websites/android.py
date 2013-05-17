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

def check_android_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'android', None, '', True, False

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('.android.clients.google.com') > -1 and path.find('market/GetBinary/') > -1:
        try:
            video_id = urllib.quote('_'.join(urllib.unquote(path).strip('/').split('/')[-2:]) + '.android')
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

