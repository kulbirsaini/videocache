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
import stat
import statvfs
import subprocess

def generalized_cached_url(o, video_id, website_id, format, params = {}):
    found, dir, size, index, cached_url = False, '', '-', '', ''
    filename = video_id + format
    for dir in o.base_dirs[website_id]:
        try:
            video_path = os.path.join(dir, filename)
            if os.path.isfile(video_path):
                size = os.path.getsize(video_path)
                os.utime(video_path, None)
                if len(o.base_dirs[website_id]) > 1: index = str(o.base_dirs[website_id].index(dir))
                cached_url = o.redirect_code + ':' + os.path.join(o.cache_url, o.cache_alias, index, o.website_cache_dir[website_id], filename)
                return (True, filename, dir.rstrip(o.website_cache_dir[website_id]), size, index, cached_url)
        except Exception, e:
            continue
    return (False, filename, '', '-', '', '')

def free_space(dir):
    disk_stat = os.statvfs(dir)
    return disk_stat[statvfs.F_FRSIZE] * disk_stat[statvfs.F_BAVAIL] / (1024*1024.0)

def partition_size(dir):
    disk_stat = os.statvfs(dir)
    return disk_stat[statvfs.F_FRSIZE] * disk_stat[statvfs.F_BLOCKS] / (1024*1024.0)

def partition_used(dir):
    disk_stat = os.statvfs(dir)
    return (disk_stat[statvfs.F_BLOCKS] - disk_stat[statvfs.F_BFREE]) * disk_stat[statvfs.F_FRSIZE] / (1024.0*1024)

def get_size_and_time(filename):
    file_stat = os.stat(filename)
    return (file_stat[stat.ST_SIZE], file_stat[stat.ST_ATIME])

def get_filelist(dir, sort_by = 'time', order = 'desc'):
    cmd = "find %s -type f ! -iname '*.xml' ! -iname '*.queue' -printf " % dir

    if sort_by == 'size':
        cmd += '"%b %AY%Am%Ad%AH%AM%AS %p\\n"'
    else:
        cmd += '"%AY%Am%Ad%AH%AM%AS %b %p\\n"'

    cmd += " | sort -n"

    if order == 'desc': cmd += 'r'

    cmd += " | head -10000 2> /dev/null"
    filelist = []
    try:
        co = subprocess.Popen([cmd], shell = True, stdout = subprocess.PIPE)
        output = co.stdout.read().strip('\n').split('\n')
        for line in output:
            filename = line.strip().split(' ')[2]
            if filelist != '':
                filelist.append(filename)
        if co.poll() is None: co.terminate()
        return filelist
    except Exception, e:
        pass
    return filelist

