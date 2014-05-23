#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os

def get_generalized_filename(o, video_id, format):
    return video_id + format

def generalized_cached_url(o, video_id, website_id, format, params = {}):
    found, directory, size, index, cached_url = False, '', '-', '', ''
    filename = video_id + format
    for directory in o.base_dirs[website_id]:
        try:
            video_path = os.path.join(directory, filename)
            if os.path.isfile(video_path):
                size = os.path.getsize(video_path)
                os.utime(video_path, None)
                if len(o.base_dirs[website_id]) > 1: index = str(o.base_dirs[website_id].index(directory))
                cached_url = o.redirect_code + ':' + os.path.join(o.cache_url, o.cache_alias, index, o.website_cache_dir[website_id], filename)
                return (True, filename, directory.rstrip(o.website_cache_dir[website_id]), size, index, cached_url)
        except Exception, e:
            continue
    return (False, filename, '', '-', '', '')

def free_space(directory):
    disk_stat = os.statvfs(directory)
    return disk_stat.f_frsize * disk_stat.f_bavail / 1048576.0

def partition_size(directory):
    disk_stat = os.statvfs(directory)
    return disk_stat.f_frsize * disk_stat.f_blocks / 1048576.0

def partition_used(directory):
    disk_stat = os.statvfs(directory)
    return (disk_stat.f_blocks - disk_stat.f_bfree) * disk_stat.f_frsize / 1048576.0

def get_size_and_time(filename):
    file_stat = os.stat(filename)
    return (file_stat.st_size, file_stat.st_atime)
