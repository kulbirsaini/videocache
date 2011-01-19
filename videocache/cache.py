#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *
from error_codes import *
from fork import *

import cookielib
import os
import socket
import sys
import traceback
import urllib2
import urlparse

# Cookie processor and default socket timeout
cj = cookielib.CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)))
socket.setdefaulttimeout(120)

def video_params_all((base_path, base_path_size), video_id, type, index = ''):
    if len(base_dir) == 1:
        index = ''
    type_low = type.lower()
    path = os.path.join(base_path, eval(type_low + '_cache_dir'), video_id)
    max_size = eval('max_' + type_low + '_video_size')
    min_size = eval('min_' + type_low + '_video_size')
    cache_dir = os.path.join(base_path, eval(type_low + '_cache_dir'))
    tmp_cache = os.path.join(base_path, temp_dir)
    return (path, max_size, min_size, base_path_size, cache_dir, tmp_cache)

def download_youtube_video(args):
    [index, client, video_id, path, tmp_cache, type, format_id, mode] = args
    pid = os.getpid()
    request = urllib2.Request('http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id, None, std_headers)
    try:
        webpage = urllib2.urlopen(request).read()
    except Exception, e:
        log(format%(pid, client, video_id, 'VIDEO_PAGE_ERR', type, ' Error occured while fetching video webpage. ' + str(e)))
        return None

    for el in ['&el=detailpage', '&el=embedded', '&el=vevo', '']:
        info_url = 'http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el)
        request = urllib2.Request(info_url, None, std_headers)
        try:
            info_page = urllib2.urlopen(request).read()
            info = cgi.parse_qs(info_page)
            if 'fmt_url_map' in info:
                break
        except Exception, e:
            log(format%(pid, client, video_id, 'VIDEO_INFO_ERR', type, ' Error occured while fetching video info.'))
            return None

    alternate_ids = []
    video_url = None
    try:
        if 'fmt_url_map' in info:
            urls = [ u.split('|')[1] for u in info['fmt_url_map'][0].split(',') ]
            video_url = urls[0]
            for url in urls:
                vid = get_new_video_id(url)
                if vid and vid not in alternate_ids:
                    alternate_ids.append(vid)
    except Exception, e:
        log(format%(pid, client, video_id, 'ALTERNATE_VIDEO_ID_ERROR', type, ' Error occured while fetching alternate video id. ' + str(e)))


    if not video_url:
        log(format%(pid, client, video_id, 'VIDEO_URL_ERR', type, ' Error occured while determining video URL.'))
        return

    try:
        download_path = os.path.join(tmp_cache, os.path.basename(path))
        if not os.path.exists(path):
            result = cache_remote_url(video_url, download_path)
            if result[0]:
                size = os.path.getsize(download_path)
                os.rename(download_path, path)
                os.chmod(path, mode)
                os.utime(path, None)
                log(format%(pid, client, video_id, 'DOWNLOAD', type, str(size) + ' Video was downloaded and cached.'))
            else:
                log(format%(pid, client, video_id, result[1], type, result[2]))
        else:
            log(format%(pid, client, video_id, 'VIDEO_EXISTS', type, ' Video already exists.'))

        for vid in alternate_ids:
            try:
                (new_path, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params_all(base_dir[index], vid, type, index)
                if new_path is not None:
                    if not os.path.exists(new_path):
                        os.link(path, new_path)
                    os.utime(new_path, None)
            except Exception, e:
                log(format%(pid, client, video_id, 'ALTERNATE_LINK_ERR', type, str(e)))
                continue
        remove(video_id)
        return True
    except Exception, e:
        log(format%(pid, client, video_id, 'DOWNLOAD_ERR', type, ' Error while caching video. ' + str(e)))
    return None

def download_from_source(args):
    """This function downloads the file from remote source and caches it."""
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    mode = 0644
    pid = os.getpid()
    try:
        [client, urls, video_id, type] = args
    except Exception, e:
        log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', str(e)))
        return

    index = None
    for base_tup in base_dir:
        # Pick up cache directories one by one.
        try:
            (path, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params_all(base_tup, video_id, type, base_dir.index(base_tup))
        except Exception, e:
            log(format%(pid, client, video_id, 'PARAM_ERR', type, str(e)))
            continue

        # Check the disk space left in the partition with cache directory.
        disk_stat = os.statvfs(cache_dir)
        disk_available = disk_stat[statvfs.F_BSIZE] * disk_stat[statvfs.F_BAVAIL] / (1024*1024.0)
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        # If disk availability reached disk_avail_threshold, then we can't use this cache anymore.
        if disk_available < disk_avail_threshold:
            log(format%(pid, client, video_id, 'CACHE_FULL', type, 'Cache directory \'' + base_tup[0] + '\' has reached the disk availability threshold.'))
            # Check next cache directory
            continue
        else:
            index = base_dir.index(base_tup)
            # Search complete. Just write wherever possible.
            break

    if index is not None:
        (path, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params_all(base_dir[index], video_id, type, index)
    else:
        # No idea what went wrong.
        print >>sys.stderr, 'Videocache: Warning: Something wrong with cache directories.'
        remove(video_id)
        return

    for url in urls:
        original_url = url
        url = refine_url(url, ['begin', 'start', 'noflv'])
        try:
            if type == 'YOUTUBE':
                format_id = get_youtube_video_format(url)
                return download_youtube_video([index, client, video_id, path, tmp_cache, type, format_id, mode])
            if not os.path.exists(path):
                download_path = os.path.join(tmp_cache, os.path.basename(path))
                result = cache_remote_url(url, download_path)
                if result[0]:
                    size = os.path.getsize(download_path)
                    os.rename(download_path, path)
                    os.chmod(path, mode)
                    os.utime(path, None)
                    log(format%(pid, client, video_id, 'DOWNLOAD', type, str(size) + ' Video was downloaded and cached.'))
                else:
                    log(format%(pid, client, video_id, result[1], type, result[2]))
            else:
                log(format%(pid, client, video_id, 'VIDEO_EXISTS', type, ' Video already exists.'))
            remove(video_id)
            return
        except Exception, e:
            if urls.index(original_url) == len(urls) - 1:
                remove(video_id)
            log(format%(pid, client, video_id, 'DOWNLOAD_ERR', type, str(e)))
    return

def cache_remote_url(remote_url, target_file):
    request = urllib2.Request(remote_url, None, std_headers)
    connection = urllib2.urlopen(request)
    try:
        file = None
        while True:
            block = connection.read(32768)
            if len(block) == 0:
                break
            if not file:
                file = open(target_file, 'wb')
            file.write(block)
        if file:
            file.close()
    except urllib2.HTTPError, e:
        try:
            return { 'success' : False, 'code' : CACHE_HTTP_ERR, 'message' : 'HTTP error : ' + str(e.code) + '. An error occured while caching the video at '  + remote_url + '.', 'debug' : str(e), 'trace' : traceback.format_exc() }
        except:
            return { 'success' : False, 'code' : CACHE_HTTP_ERR, 'message' : 'HTTP error. An error occured while caching the video at '  + remote_url + '.', 'debug' : str(e), 'trace' : traceback.format_exc() }
    except Exception, e:
        return { 'success' : False, 'code' : CACHE_ERR, 'message' : 'Could not cache the video at ' + remote_url + '.', 'debug' : str(e), 'trace' : traceback.format_exc() }
    return { 'success' : True }

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, params] = [fragments[1], fragments[2], fragments[3]]

    arglist = params.split('&')
    dict = {}
    for arg in arglist:
        try:
            dict[arg.split('=')[0]] = arg.split('=')[1]
        except Exception, e:
            continue
    if dict.has_key('fmt'):
        format_id = dict['fmt']
    elif dict.has_key('itag'):
        format_id = dict['itag']
    else:
        format_id = 34
    return format_id


def get_new_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, params] = [fragments[1], fragments[2], fragments[3]]

    arglist = params.split('&')
    dict = {}
    for arg in arglist:
        try:
            dict[arg.split('=')[0]] = arg.split('=')[1]
        except Exception, e:
            continue
    if dict.has_key('video_id'):
        video_id = dict['video_id']
    elif dict.has_key('docid'):
        video_id = dict['docid']
    elif dict.has_key('id'):
        video_id = dict['id']
    else:
        video_id = None
    return video_id

