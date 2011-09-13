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
from vcoptions import VideocacheOptions
from vcsysinfo import *

from optparse import OptionParser
from xmlrpclib import ServerProxy

import cgi
import logging
import logging.handlers
import os
import re
import subprocess
import sys
import syslog
import threading
import time
import traceback
import urllib
import urllib2
import urlparse

def info(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.INFO), 'process_id' : process_id})
        o.vc_logger.info(build_message(params))

def error(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.ERROR), 'process_id' : process_id})
        o.vc_logger.error(build_message(params))

def warn(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.WARN), 'process_id' : process_id})
        o.vc_logger.debug(build_message(params))

def trace(params = {}):
    if o.enable_trace_log:
        params.update({ 'logformat' : o.trace_logformat, 'timeformat' : o.timeformat, 'process_id' : process_id })
        o.trace_logger.info(build_message(params))

def sync_video_info():
    global local_video_pool
    info({ 'code' : VIDEO_SYNC_START, 'message' : 'Starting sync thread to sync video information to RPC server.'})
    connection()
    videos = {}
    sleep_time = 5
    while True:
        try:
            thread_pool.acquire()
            videos.update( local_video_pool )
            local_video_pool = {}
            thread_pool.release()
            if videos:
                num_tries = 0
                while videos and num_tries < 5:
                    try:
                        video_pool.ping()
                        if submit_videos(videos):
                            videos = {}
                            break
                    except Exception, e:
                        connection()

                    for i in range(1, int(min(2 ** num_tries, 10) / 0.1)):
                        if exit:
                            info({ 'code' : VIDEO_SYNC_STOP, 'message' : 'Stopping sync thread.'})
                            return
                        time.sleep(0.1)
                    num_tries += 1
                else:
                    warn({ 'code' : VIDEO_SUBMIT_FAIL, 'message' : 'Could not submit video information to videocache scheduler at ' + o.rpc_host + ':' + str(o.rpc_port) + '. Please check scheduler status. If needed, restart scheduler using \'vc-scheduler -s restart\' command.' })
        except Exception, e:
            warn({ 'code' : VIDEO_SUBMIT_WARN, 'message' : 'Error in updating server with video inforation. Continuing.', 'debug' : str(e)})
            trace({ 'code' : VIDEO_SUBMIT_WARN, 'message' : traceback.format_exc() })
        for i in range(1, int(sleep_time / 0.1)):
            if exit:
                info({ 'code' : VIDEO_SYNC_STOP, 'message' : 'Stopping sync thread.'})
                return
            time.sleep(0.1)

def submit_system_info():
    time.sleep(10)
    expired_video(o)
    try:
        num_tries = 0
        while num_tries < 5:
            try:
                video_pool.ping()
                sys_info = { 'id' : o.id, 'email' : o.client_email, 'version' : o.version }
                sys_info.update(get_all_info())
                video_pool.add_system(sys_info)
                return True
            except Exception, e:
                connection()

            for i in range(1, int(min(2 ** num_tries, 10) / 0.1)):
                if exit:
                    return False
                time.sleep(0.1)
            num_tries += 1
        else:
            return False
    except Exception, e:
        return False

def check_apache():
    ret_val = True
    try:
        if o.cache_host_ip and o.cache_host_port and not is_port_open(o.cache_host_ip, o.cache_host_port):
            error({ 'code' : APACHE_CONNECT_ERR, 'message' : 'Could not connect to Apache webserver on ' + o.cache_host_ip + ':' + str(o.cache_host_port) + '. Please check if Apache is running. Also, verify the value of cache_host option in /etc/videocache.conf.' })
            return False
        for dir in o.base_dir_list:
            if len(o.base_dir_list) > 1:
                index = o.base_dir_list.index(dir)
            else:
                index = ''
            cache_url = os.path.join(o.cache_url, 'videocache', str(index))
            result = test_url(cache_url)
            if result == 404:
                error({ 'code' : APACHE_404_ERR, 'message' : 'HTTP 404 or Not Found error occurred while navigating to ' + cache_url + '. If you changed base_dir option in /etc/videocache.conf, please run vc-update and restart Apache webserver. And finally reload/restart Squid daemon.', 'debug' : 'Videocache Directory: ' + dir })
            elif result == 403:
                error({ 'code' : APACHE_403_ERR, 'message' : 'HTTP 403 or Access Denied while navigating to ' + cache_url + '. Please verify that Apache has read access to the following directory ' + dir + '. If you changed base_dir option in /etc/videocache.conf, please run vc-update and restart Apache webserver. And finally reload/restart Squid daemon.' })
            elif result == False:
                ret_val = result
    except Exception, e:
        return False
    return ret_val

def check_heartbeat():
    sleep_time = 900
    while True:
        check_apache()
        if not submit_system_info():
            sleep_time = 1800

        for i in range(1, sleep_time):
            if exit:
                return
            time.sleep(1)

def submit_videos(videos):
    try:
        video_pool.add_videos(videos)
        info({ 'code' : VIDEO_SUBMIT, 'message' : 'Submitted ' + str(len(videos)) + ' videos to videocache scheduler.'})
        return True
    except Exception, e:
        error({ 'code' : VIDEO_SUBMIT_ERR, 'message' : 'Could not submit video information to videocache scheduler.', 'debug' : str(e)})
        trace({ 'code' : VIDEO_SUBMIT_ERR, 'message' : traceback.format_exc() })
    return False

def connection():
    global video_pool
    try:
        video_pool.ping()
    except Exception, e:
        try:
            video_pool = ServerProxy(o.rpc_url)
            video_pool.ping()
            info({ 'code' : RPC_CONNECT, 'message' : 'Connected to RPC server.'})
        except Exception, e:
            error({ 'code' : RPC_CONNECT_ERR, 'message' : 'Could not connect to RPC server (videocache scheduler) at ' + o.rpc_host + ':' + str(o.rpc_port) + '. Please check scheduler status. If needed, restart scheduler using \'vc-scheduler -s restart\' command.', 'debug' : str(e)})
            trace({ 'code' : RPC_CONNECT_ERR, 'message' : traceback.format_exc() })

def add_video_to_local_pool(video_id, params):
    global local_video_pool
    thread_pool.acquire()
    if video_id in local_video_pool:
        local_video_pool[video_id].append(params)
    else:
        local_video_pool[video_id] = [params]
    thread_pool.release()

def cache_video(client_ip, website_id, url, video_id, cache_check_only = False, format = ''):
    info( { 'code' : URL_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : url } )

    video_id = urllib.unquote(video_id)
    try:
        video_id.decode('ascii')
    except Exception, e:
        warn( { 'code' : VIDEO_ID_ENCODING, 'message' : 'Video ID contains non-ascii characters. Will not process this.', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )
        trace( { 'code' : VIDEO_ID_ENCODING, 'message' : traceback.format_exc(), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )
        return ('', 0)

    try:
        for dir in o.base_dirs[website_id]:
            video_path = os.path.join(dir, video_id) + format
            if os.path.isfile(video_path):
                if website_id == 'youtube':
                    try:
                        fp = open(video_path, 'rb')
                        header_data = fp.read(300)
                        fp.close()
                        if re.compile('webm', re.I).search(header_data):
                            os.unlink(video_path)
                            continue
                    except Exception, e:
                        pass
                try:
                    size = os.path.getsize(video_path)
                except:
                    size = '-'
                os.utime(video_path, None)
                if len(o.base_dirs[website_id]) > 1:
                    index = o.base_dirs[website_id].index(dir)
                else:
                    index = ''
                query = urlparse.urlsplit(url)[3]
                cached_url = os.path.join(o.cache_url, 'videocache', str(index), website_id)
                url = os.path.join(cached_url, urllib.quote(video_id)) + format + '?' + query
                new_url = o.redirect_code + ':' + refine_url(url, ['noflv'])
                return (new_url, size)
    except Exception, e:
        warn( { 'code' : VIDEO_SEARCH_WARN, 'message' : 'Could not search video in local cache.', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )
        trace( { 'code' : VIDEO_SEARCH_WARN, 'message' : traceback.format_exc(), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )

    if not cache_check_only:
        add_video_to_local_pool(video_id, {'video_id' : video_id, 'client_ip' : client_ip, 'urls' : [url], 'website_id' : website_id, 'access_time' : time.time(), 'format' : format})
    return ('', 0)

def squid_part():
    global exit
    input = sys.stdin.readline()
    while input:
        new_url = ''
        skip = False
        try:
            fields = input.strip().split(' ')
            if o.cache_host == '':
                error( { 'code' : CACHE_HOST_ERR, 'message' : 'The option cache_host in /etc/videocache.conf is not set. Please set it and restart/reload Squid daemon. Videocache will be disabled until you set cache_host.' } )
                skip = True
            if len(fields) < 4:
                warn( { 'code' : INPUT_WARN, 'message' : 'Input received from Squid is not parsable. Skipping this URL.' } )
                skip = True
            elif fields[3].upper() != 'GET':
                warn( { 'code' : HTTP_METHOD_WARN, 'message' : 'Can\'t handle HTTP method ' + fields[3].upper() + '. Skipping this URL.' } )
                skip = True
            else:
                url = fields[0]
                client_ip = fields[1].split('/')[0]
                fragments = urlparse.urlsplit(fields[0])
                if (fragments[0] != 'http' and fragments[0] != 'https') or fragments[1] == '' or fragments[2] == '':
                    warn( { 'code' : URL_WARN, 'client_ip' : client_ip, 'message' : 'Can\'t process. Skipping this URL ' + url } )
                    skip = True
                else:
                    [host, path, query] = [fragments[1], fragments[2], fragments[3]]
        except Exception, e:
            warn( { 'code' : INPUT_PARSE_ERR, 'message' : 'Could not get required informatoin after parsing the input. Skipping this URL.', 'debug' : str(e) } )
            trace( { 'code' : INPUT_PARSE_ERR, 'message' : traceback.format_exc() } )
            skip = True

        if o.client_email != '':
            if not skip and o.enable_videocache:
                matched = False
                # Youtube.com ang Google Video caching is handled here.
                if not matched and o.enable_youtube_cache:
                    if (path.find('get_video') > -1 or path.find('watch') > -1 or path.find('watch_popup') > -1) and path.find('get_video_info') < 0 and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
                        website_id = 'youtube'
                        matched = True
                        video_id = get_youtube_video_id_from_query(query)
                        format = get_youtube_video_format_from_query(query)

                        if format == 18:
                            format = '_18.mp4'
                        else:
                            format = ''

                        if video_id is not None:
                            cache_video(client_ip, website_id, url, video_id, False, format)
                        else:
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

                # Youtube.com ang Google Video caching is handled here. URLs with e/v/embed
                if not matched and o.enable_youtube_cache:
                    if re.compile('\/(v|e|embed)\/([0-9a-zA-Z_-]{11})').search(path) and path.find('get_video_info') < 0 and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
                        website_id = 'youtube'
                        matched = True
                        format = get_youtube_video_format_from_query(query)

                        if format == 18:
                            format = '_18.mp4'
                        else:
                            format = ''

                        try:
                            video_id = re.compile('\/(v|e|embed)\/([0-9a-zA-Z_-]{11})').search(path).group(2)
                        except Exception, e:
                            video_id = None

                        if video_id is not None:
                            cache_video(client_ip, website_id, url, video_id, False, format)
                        else:
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

                # Youtube.com and Google Video for mobile API requests
                if not matched and o.enable_youtube_cache:
                    if re.compile('\/feeds\/api\/videos\/[0-9a-zA-Z_-]{11}\/').search(path) and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
                        website_id = 'youtube'
                        matched = True
                        format = '_18.mp4'
                        try:
                            video_id = re.compile('\/feeds\/api\/videos\/([0-9a-zA-Z_-]{11})\/').search(path).group(1)
                        except Exception, e:
                            video_id = None

                        if video_id is not None:
                            cache_video(client_ip, website_id, url, video_id, False, format)
                        else:
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

                # Youtube.com and Google Video caching is handled here. URLs with videoplayback.
                if not matched and o.enable_youtube_cache:
                    if path.find('videoplayback') > -1 and path.find('get_video_info') < 0 and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
                        website_id = 'youtube'
                        matched = True
                        video_id = get_youtube_video_id_from_query(query)
                        format = get_youtube_video_format_from_query(query)

                        if format == 18:
                            format = '_18.mp4'
                        else:
                            format = ''

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id, True, format)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )
                        else:
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

                # AOL.com caching is handled here.
                if not matched and o.enable_aol_cache:
                    if host.find('stream.aol.com') > -1 and re.compile('(.*)/[a-zA-Z0-9]+\/(.*)\.(flv)').search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
                        website_id = 'aol'
                        matched = True
                        try:
                            video_id = '_'.join(path.strip('/').split('/')[-2:])
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Bing.com caching is handled here.
                if not matched and o.enable_bing_cache:
                    if (host.find('msn.com') > -1 or re.compile('msnbc\.(.*)\.(com|net)').search(host) or re.compile('msn\.(.*)\.(com|net)').search(host)) and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'bing'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Blip.tv Video file caching is handled here.
                if not matched and o.enable_bliptv_cache:
                    if path.find('filename=') < 0 and re.compile('\.video[a-z0-9]?[a-z0-9]?[a-z0-9]?\.blip\.tv').search(host) and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'bliptv'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Break.com Video file caching is handled here.
                if not matched and o.enable_break_cache:
                    if host.find('.break.com') > -1 and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'break'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # CNN.com caching is handled here.
                if not matched and o.enable_cnn_cache:
                    if host.find('cdn.turner.com') > -1 and re.compile('(.*)/(.*)\.(flv)').search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
                        website_id = 'cnn'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Dailymotion.com caching is handled here.
                if not matched and o.enable_dailymotion_cache:
                    if host.find('.dailymotion.com') > -1 and (re.compile('/video/[a-zA-Z0-9]{5,9}_?.*').search(path)):
                        website_id = 'dailymotion'
                        matched = True
                        try:
                            video_id = re.compile('/video/([a-zA-Z0-9]{5,9})_?.*').search(path).group(1) + '.mp4'
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            cache_video(client_ip, website_id, url, video_id, False)
                        else:
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

                # Dailymotion.com caching is handled here.
                if not matched and o.enable_dailymotion_cache:
                    if (host.find('vid.akm.dailymotion.com') > -1 or re.compile('proxy[a-z0-9\-]?[a-z0-9]?[a-z0-9]?[a-z0-9]?\.dailymotion\.com').search(host)) and (path.find('.mp4') > -1 or path.find('.on2') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'dailymotion'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                            video_id = video_id.replace('_hq.mp4', '.mp4')
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id, True)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Facebook.com caching is handled here.
                if not matched and o.enable_facebook_cache:
                    if re.compile('video\.(.*)\.fbcdn\.net').search(host) and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'facebook'
                        matched = True
                        try:
                            video_id = urllib.unquote(path).strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Megavideo.com caching is handled here.
                if not matched and o.enable_megavideo_cache:
                    if host.find('megavideo.com') > -1:
                        website_id = 'megavideo'
                        matched = True
                        try:
                            dict = cgi.parse_qs(query)
                            video_id = dict.get('v', None)
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Metacafe.com caching is handled here.
                if not matched and o.enable_metacafe_cache:
                    if (host.find('.mccont.com') > -1 or host.find('akvideos.metacafe.com') > -1 ) and path.find('ItemFiles') > -1 and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'metacafe'
                        matched = True
                        try:
                            video_id = urllib.unquote(path).strip('/').split(' ')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # MySpace.com caching is handled here.
                if not matched and o.enable_myspace_cache:
                    if (re.compile('(.*)\.myspacecdn\.com').search(host) or re.compile('(.*)\.myspacecdn\.(.*)\.footprint\.net').search(host)) and re.compile('(.*)\/[a-zA-Z0-9]+\/vid\.mp4').search(path) and path.find('.mp4') > -1:
                        website_id = 'myspace'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-2] + '.mp4'
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Vimeo.com caching is handled here.
                if not matched and o.enable_vimeo_cache:
                    if (host.find('.vimeo.com') > -1 or (host.find('.amazonaws.com') > -1 and path.find('.vimeo.com') > -1)) and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'vimeo'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Wrzuta.pl audio file caching is handled here.
                if not matched and o.enable_wrzuta_cache:
                    try:
                        if host.find('c.wrzuta.pl') > -1:
                            video_id = None
                            website_id = 'wrzuta'
                            if re.compile('[a-z]a[0-9][0-9]?[0-9]?[0-9]?[0-9]?').search(path):
                                matched = True
                                try:
                                    video_id = path.strip('/').split('/')[-1]
                                except Exception, e:
                                    video_id = None
                                    warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                                    trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )
                            elif (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                                matched = True
                                try:
                                    video_id = path.strip('/').split('/')[-1]
                                except Exception, e:
                                    video_id = None
                                    warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                                    trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )
                            if video_id is not None:
                                new_url, size = cache_video(client_ip, website_id, url, video_id)
                                if new_url == '':
                                    info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                                else:
                                    info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )
                    except Exception, e:
                        trace( { 'message' : traceback.format_exc() } )

                # Pr0n sites
                # Extremetube.com caching is handled here.
                if not matched and o.enable_extremetube_cache:
                    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.extremetube\.phncdn\.com').search(host) and re.compile('(.*)\/[a-zA-Z0-9_-]+\.flv').search(path) and path.find('.flv') > -1:
                        website_id = 'extremetube'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Hardsextube.com caching is handled here.
                if not matched and o.enable_hardsextube_cache:
                    if re.compile('vs[a-z0-9]?[a-z0-9]?[a-z0-9]?\.hardsextube\.com').search(host) and re.compile('(.*)\/(.*)\.flv').search(path) and path.find('.flv') > -1:
                        website_id = 'hardsextube'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Keezmovies.com caching is handled here.
                if not matched and o.enable_keezmovies_cache:
                    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.keezmovies\.com').search(host) and re.compile('(.*)\/[0-9]+\.flv').search(path) and path.find('.flv') > -1:
                        website_id = 'keezmovies'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Pornhub.com caching is handled here.
                if not matched and o.enable_pornhub_cache:
                    if re.compile('nyc-v[a-z0-9]?[a-z0-9]?[a-z0-9]?\.pornhub\.com').search(host) and re.compile('(.*)/videos/[0-9]{3}/[0-9]{3}/[0-9]{3}/[0-9]+\.(flv)').search(path) and path.find('.flv') > -1:
                        website_id = 'pornhub'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Redtube.com caching is handled here.
                if not matched and o.enable_redtube_cache:
                    if host.find('.redtubefiles.com') > -1 and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'redtube'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Slutload.com caching is handled here.
                if not matched and o.enable_slutload_cache:
                    if re.compile('\.slutload-media\.com').search(host) and re.compile('(.*)\/[a-zA-Z0-9_-]+\.flv').search(path) and path.find('.flv') > -1:
                        website_id = 'slutload'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Spankwire.com caching is handled here.
                if not matched and o.enable_spankwire_cache:
                    if re.compile('cdn[a-z0-9]?[a-z0-9]?[a-z0-9]?\.public\.spankwire\.com').search(host) and re.compile('(.*)\/(.*)\.flv').search(path) and path.find('.flv') > -1:
                        website_id = 'spankwire'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Tube8.com Video file caching is handled here.
                if not matched and o.enable_tube8_cache:
                    if host.find('.tube8.com') > -1 and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'tube8'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Xhamster.com caching is handled here.
                if not matched and o.enable_xhamster_cache:
                    if re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host) and re.compile('\/flv2\/[0-9]+:(.*)\/(.*)\.flv').search(path) and path.find('.flv') > -1:
                        website_id = 'xhamster'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Xtube.com caching is handled here.
                if not matched and o.enable_xtube_cache:
                    if (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1) and path.find('Thumb') < 0 and path.find('av_preview') < 0 and re.compile('\.xtube\.com').search(host):
                        website_id = 'xtube'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Xvideos.com caching is handled here.
                if not matched and o.enable_xvideos_cache:
                    if re.compile('porn[a-z0-9][a-z0-9]?[a-z0-9]?[a-z0-9]?\.xvideos\.com').search(host) and re.compile('videos\/flv\/(.*)\/(.*)\.(flv|mp4)').search(path) and (path.find('.flv') > -1 or path.find('.mp4') > -1):
                        website_id = 'xvideos'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1].split('_')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )

                # Youporn.com caching is handled here.
                if not matched and o.enable_youporn_cache:
                    if host.find('.youporn.com') > -1 and (path.find('.mp4') > -1 or path.find('.flv') > -1 or path.find('.mov') > -1 or path.find('.mkv') > -1 or path.find('.avi') > -1 or path.find('.rm') > -1 or path.find('.rmvb') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1 or path.find('.wmv') > -1 or path.find('.mpg') > -1 or path.find('.mpeg') > -1 or path.find('.3gp') > -1):
                        website_id = 'youporn'
                        matched = True
                        try:
                            video_id = path.strip('/').split('/')[-1]
                        except Exception, e:
                            video_id = None
                            warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                            trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                        if video_id is not None:
                            new_url, size = cache_video(client_ip, website_id, url, video_id)
                            if new_url == '':
                                info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
                            else:
                                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )
        else:
            warn( { 'code' : 'RRE_LIAME_TNEILC'[::-1], 'message' : '.reludehcs-cv tratser ,oslA .diuqS tratser/daoler dna noitpo siht teS .tes ton si fnoc.ehcacoediv/cte/ ni liame_tneilc noitpo ehT'[::-1] } )

        try:
            sys.stdout.write(new_url + '\n')
            sys.stdout.flush()
        except Exception, e:
            warn( { 'code' : WRITEBACK_ERR, 'message' : 'Could not send a reply message to Squid server.', 'debug' : str(e) } )
            trace( { 'code' : WRITEBACK_ERR, 'message' : traceback.format_exc() } )
        input = sys.stdin.readline()
    else:
        info( { 'code' : VIDEOCACHE_EXIT, 'message' : 'Received a stop signal from Squid server. Stopping Videocache.' } )
        exit = True

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-p', '--prefix', dest = 'vc_root', type='string', help = 'Specify an alternate root location for videocache', default = '/')
    parser.add_option('-c', '--config', dest = 'config_file', type='string', help = 'Use an alternate configuration file', default = '/etc/videocache.conf')
    options, args = parser.parse_args()

    halt_message = 'One or more errors while starting Videocache. Please check syslog and videocache log for errors.'
    try:
        root = options.vc_root 
        o = VideocacheOptions(options.config_file, root)
    except Exception, e:
        syslog_msg( halt_message + ' Debug: '  + traceback.format_exc().replace('\n', ''))
        sys.exit(1)

    if o.halt or o.set_loggers() == None:
        syslog_msg(halt_message)
        sys.exit(1)

    local_video_pool = {}
    video_pool = None
    thread_pool = threading.Semaphore(value = 1)
    process_id = os.getpid()
    exit = False

    if o.cache_host == '':
        error( { 'code' : CACHE_HOST_ERR, 'message' : 'The option cache_host in /etc/videocache.conf is not set. Please set it and restart/reload Squid daemon. Videocache will be disabled until you set cache_host.' } )
        o.enable_videocache = 0
    elif re.compile('127.0.0.1').search(o.cache_host):
        warn( { 'code' : CACHE_HOST_WARN, 'message' : 'The option cache_host is set to 127.0.0.1. Videocache will be able to serve videos only to localhost. Please set it to the private/public IP address of the server and restart/reload Squid daemon' } )

    info( { 'code' : VIDEOCACHE_START, 'message' : 'Starting Videocache.' } )

    try:
        squid = threading.Thread(target = squid_part)
        video_info = threading.Thread(target = sync_video_info)
        system_info = threading.Thread(target = check_heartbeat)
        squid.start()
        video_info.start()
        system_info.start()
        squid.join()
        video_info.join()
        system_info.join()
    except Exception, e:
        error( { 'code' : VIDEOCACHE_RUNTIME_ERR, 'message' : 'Encountered an error while in service.', 'debug' : str(e) } )
        trace( { 'code' : VIDEOCACHE_RUNTIME_ERR, 'message' : traceback.format_exc() } )

