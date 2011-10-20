#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from error_codes import *

import os

def search_cache(o, website_id, video_id, format):
    for dir in o.base_dirs[website_id]:
        video_path = os.path.join(dir, video_id) + format
        if os.path.isfile(video_path):
            return True
    return False

