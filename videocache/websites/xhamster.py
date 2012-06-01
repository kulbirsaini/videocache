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
import sys
import urllib
import urlparse

root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, root_dir)
from common import is_valid_ip

def check_xhamster_video(url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'xhamster', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    if is_valid_ip(host) and re.compile('(.*)key=[a-zA-Z0-9]+(.*)\.flv').search(path):
        try:
            video_id = urllib.quote(re.compile('.*key=([a-z0-9A-Z]+).*').search(path).groups()[0])
        except Exception, e:
            pass
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

