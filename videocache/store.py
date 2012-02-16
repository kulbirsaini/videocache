#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from error_codes import *

import os
import statvfs
import subprocess

def search_cache(o, website_id, video_id, format):
    for dir in o.base_dirs[website_id]:
        video_path = os.path.join(dir, video_id) + format
        if os.path.isfile(video_path):
            return True
    return False

def free_space(dir):
    disk_stat = os.statvfs(dir)
    return disk_stat[statvfs.F_FRSIZE] * disk_stat[statvfs.F_BAVAIL] / (1024*1024.0)

def get_filelist(dir, sort_by = 'time', order = 'desc'):
    cmd = 'ls -1d'

    if sort_by == 'size':
        cmd += 'S'
    else:
        cmd += 't'

    if order == 'asc': cmd += 'r'

    cmd += ' ' + dir + ' 2> /dev/null'
    for path in ['', '/bin/']:
        command = os.path.join(path, cmd)
        try:
            co = subprocess.Popen([command], shell = True, stdout = subprocess.PIPE)
            filelist = co.stdout.read().strip('\n').split('\n')
            while '' in filelist:
                filelist.remove('')
            if co.poll() is None: co.terminate()
            return filelist
        except Exception, e:
            continue
    return []
