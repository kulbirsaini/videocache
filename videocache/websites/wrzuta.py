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

def check_wrzuta_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'wrzuta', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if host.find('c.wrzuta.pl') > -1:
        if re.compile('wv[0-9]+\/[a-z0-9]+\/0\/').search(path):
            try:
                video_id = urllib.quote(path.strip('/').split('/')[-2])
            except Exception, e:
                pass
        elif re.compile('wa[0-9]+\/[a-z0-9]+').search(path):
            try:
                video_id = urllib.quote(path.strip('/').split('/')[-1])
            except Exception, e:
                pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

