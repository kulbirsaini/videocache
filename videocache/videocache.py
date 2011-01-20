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

from optparse import OptionParser
from xmlrpclib import ServerProxy
import logging
import logging.handlers
import os
import re
import rpyc
import sys
import syslog
import threading
import time
import traceback
import urllib
import urlparse

def info(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.INFO), 'process_id' : process_id})
    o.vc_logger.info(build_message(params))

def error(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.ERROR), 'process_id' : process_id})
    o.vc_logger.error(build_message(params))

def warn(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.WARN), 'process_id' : process_id})
    o.vc_logger.debug(build_message(params))

def trace(params = {}):
    params.update({ 'trace_logformat' : o.trace_logformat, 'timeformat' : o.timeformat, 'process_id' : process_id })
    o.trace_logger.info(build_trace(params))

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
                    warn({ 'code' : VIDEO_SUBMIT_FAIL, 'message' : 'Could not submit video information to RPC server in ' + str(num_tries) + ' tries. Please check RPC server status.' })
        except Exception, e:
            warn({ 'code' : VIDEO_SUBMIT_WARN, 'message' : 'Error in updating server with video inforation. Continuing.', 'debug' : str(e)})
            trace({ 'code' : VIDEO_SUBMIT_WARN, 'message' : traceback.format_exc() })
        for i in range(1, int(sleep_time / 0.1)):
            if exit:
                info({ 'code' : VIDEO_SYNC_STOP, 'message' : 'Stopping sync thread.'})
                return
            time.sleep(0.1)

def submit_videos(videos):
    try:
        video_pool.add_videos(videos)
        info({ 'code' : VIDEO_SUBMIT, 'message' : 'Submitted ' + str(len(videos)) + ' videos to RPC server.'})
        return True
    except Exception, e:
        error({ 'code' : VIDEO_SUBMIT_ERR, 'message' : 'Could not submit video information to RPC server.', 'debug' : str(e)})
        trace({ 'code' : VIDEO_SUBMIT_ERR, 'message' : traceback.format_exc() })
    return False

#def connection():
#    global video_pool
#    try:
#        c = rpyc.connect(str(o.rpc_host), int(o.rpc_port))
#        video_pool = c.root
#        info({ 'code' : RPC_CONNECT, 'message' : 'Connected to RPC server.'})
#    except Exception, e:
#        error({ 'code' : RPC_CONNECT_ERR, 'message' : 'Could not connect to RPC server.', 'debug' : str(e)})
#        trace({ 'code' : RPC_CONNECT_ERR, 'message' : traceback.format_exc() })

def connection():
    global video_pool
    try:
        video_pool = ServerProxy('http://' + o.rpc_host + ':' + str(o.rpc_port))
        info({ 'code' : RPC_CONNECT, 'message' : 'Connected to RPC server.'})
    except Exception, e:
        error({ 'code' : RPC_CONNECT_ERR, 'message' : 'Could not connect to RPC server.', 'debug' : str(e)})
        trace({ 'code' : RPC_CONNECT_ERR, 'message' : traceback.format_exc() })

def add_video_to_local_pool(video_id, params):
    global local_video_pool
    thread_pool.acquire()
    if video_id in local_video_pool:
        local_video_pool[video_id].append(params)
    else:
        local_video_pool[video_id] = [params]
    thread_pool.release()

def cache_video(client_ip, website_id, url, video_id, cache_check_only = False):
    """This function check whether a video is in cache or not. If not, it fetches
    it from the remote source and cache it and also streams it to the client."""

    if not cache_check_only:
        info( { 'code' : URL_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : url } )

    try:
        for dir in o.base_dirs[website_id]:
            if os.path.isfile(os.path.join(dir, video_id)):
                os.utime(path, None)
                if len(o.base_dirs[website_id]) > 1:
                    index = o.base_dirs[website_id].index(dir)
                else:
                    index = ''
                query = urlparse.urlsplit(url)[3]
                cached_url = os.path.join(o.cache_url, 'videocache', str(index), website_id)
                url = os.path.join(cached_url, video_id) + '?' + query
                new_url = o.redirect_code + ':' + refine_url(url, ['noflv'])
                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Video was served from cache using the URL ' + new_url } )
                return new_url
    except Exception, e:
        warn( { 'code' : VIDEO_SEARCH_WARN, 'message' : 'Could not search video in local cache.', 'debug' : str(e) } )
        trace( { 'code' : VIDEO_SEARCH_WARN, 'message' : traceback.format_exc() } )

    if not cache_check_only:
        info( { 'code' : 'Adding to Local Pool' } )
        add_video_to_local_pool(video_id, {'video_id' : video_id, 'client_ip' : client_ip, 'urls' : [url], 'website_id' : website_id, 'access_time' : time.time()})
        info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
    return ''

def squid_part():
    """This function will tap requests from squid. If the request is for a
    video, they will be forwarded to function cache_video() for further processing.
    Finally this function will flush a cache_url if package found in cache or a
    blank line in case on a miss to stdout. This is the only function where we deal
    with squid, rest of the program/project doesn't interact with squid at all."""
    global exit
    input = sys.stdin.readline()
    while input:
        new_url = ''
        skip = False
        info( { 'code' : 'GOT_INPUT', 'message' : input } )
        try:
            # Read url from stdin (this is provided by squid)
            fields = input.strip().split(' ')
            if len(fields) < 4:
                warn( { 'code' : INPUT_WARN, 'message' : 'Input received from Squid is not parsable. Skipping this URL.' } )
                skip = True
            elif fields[3].upper() != 'GET':
                warn( { 'code' : HTTP_METHOD_WARN, 'message' : 'Can\'t handle HTTP method ' + fields[3].upper() + '. Skipping this URL.' } )
                skip = True
            else:
                url = fields[0]
                client_ip = fields[1].split('/')[0]
                # Retrieve the basename from the request url
                fragments = urlparse.urlsplit(fields[0])
                if (fragments[0] != 'http' and fragments[0] != 'https') or fragments[1] == '' or fragments[2] == '' or fragments[3] == '':
                    warn( { 'code' : URL_WARN, 'client_ip' : client_ip, 'message' : 'Can\'t process. Skipping this URL ' + url } )
                    skip = True
                else:
                    [host, path, query] = [fragments[1], fragments[2], fragments[3]]
        except Exception, e:
            warn( { 'code' : INPUT_PARSE_ERR, 'message' : 'Could not get required informatoin after parsing the input. Skipping this URL.', 'debug' : str(e) } )
            trace( { 'code' : INPUT_PARSE_ERR, 'message' : traceback.format_exc() } )
            skip = True

        # Check if videocache plugin is on.
        if not skip and o.enable_videocache:
            matched = False
            # Youtube.com ang Google Video caching is handled here.
            if not matched and o.enable_youtube_cache:
                if (path.find('get_video') > -1) and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.youtube\.[a-z][a-z]').search(host) or re.compile('\.youtube\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host)):
                    website_id = 'youtube'
                    matched = True
                    dict = urlparse.parse_qs(query)
                    if 'video_id' in dict:
                        video_id = dict['video_id'][0]
                    elif 'docid' in dict:
                        video_id = dict['docid'][0]
                    elif 'id' in dict:
                        video_id = dict['id'][0]
                    else:
                        video_id = None

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id, False)
                    else:
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

            # Youtube.com and Google Video caching is handled here. URLs to videoplayback.
            if not matched and o.enable_google_cache:
                if (path.find('videoplayback') > -1 or path.find('videoplay') > -1) and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.youtube\.[a-z][a-z]').search(host) or re.compile('\.youtube\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host)):
                    website_id = 'youtube'
                    matched = True
                    dict = urlparse.parse_qs(query)
                    if 'video_id' in dict:
                        video_id = dict['video_id'][0]
                    elif 'docid' in dict:
                        video_id = dict['docid'][0]
                    elif 'id' in dict:
                        video_id = dict['id'][0]
                    else:
                        video_id = None

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id, True)
                    else:
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )

            # Metacafe.com caching is handled here.
            if not matched and o.enable_metacafe_cache:
                if (host.find('.mccont.com') > -1 or host.find('akvideos.metacafe.com') > -1 ) and path.find('ItemFiles') > -1:
                    website_id = 'metacafe'
                    matched = True
                    try:
                        video_id = urllib.unquote(path).strip('/').split(' ')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Dailymotion.com caching is handled here.
            if not matched and o.enable_dailymotion_cache:
                if (path.find('.flv') > -1 or path.find('.on2') > -1 or path.find('.mp4') > -1) and (host.find('vid.akm.dailymotion.com') > -1 or host.find('.cdn.dailymotion.com') > -1 or re.compile('proxy[a-z0-9\-][a-z0-9][a-z0-9][a-z0-9]?\.dailymotion\.com').search(host)):
                    website_id = 'dailymotion'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Redtube.com caching is handled here.
            if not matched and o.enable_redtube_cache:
                if host.find('.redtube.com') > -1 and path.find('.flv') > -1:
                    website_id = 'redtube'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Xtube.com caching is handled here.
            if not matched and o.enable_xtube_cache:
                if path.find('videos/') > -1 and path.find('.flv') > -1 and path.find('Thumb') < 0 and path.find('av_preview') < 0 and re.compile('[0-9a-z][0-9a-z][0-9a-z]?[0-9a-z]?[0-9a-z]?\.xtube\.com').search(host):
                    website_id = 'xtube'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Vimeo.com caching is handled here.
            if not matched and o.enable_vimeo_cache:
                if host.find('bitcast.vimeo.com') > -1 and path.find('vimeo/videos/') > -1 and path.find('.flv') > -1:
                    website_id = 'vimeo'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Wrzuta.pl audio file caching is handled here.
            if not matched and o.enable_wrzuta_cache:
                if host.find('va.wrzuta.pl') > -1 and query.find('type=a') > -1 and query.find('key=') > -1 and re.compile('wa[0-9][0-9][0-9][0-9]?').search(path):
                    website_id = 'wrzuta'
                    matched = True
                    dict = urlparse.parse_qs(query)
                    if 'key' in dict:
                        video_id = dict['key'][0]
                        new_url = cache_video(client_ip, website_id, url, video_id)
                    else:
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )

            # Youporn.com caching is handled here.
            if not matched and o.enable_youporn_cache:
                if host.find('.files.youporn.com') > -1 and path.find('/flv/') > -1 and path.find('.flv') > -1:
                    website_id = 'youporn'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Soapbox.msn.com caching is handled here.
            if not matched and o.enable_soapbox_cache:
                if host.find('.msn.com.edgesuite.net') > -1 and path.find('.flv') > -1:
                    website_id = 'soapbox'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Tube8.com Video file caching is handled here.
            if not matched and o.enable_tube8_cache:
                if (path.find('.flv') > -1 or path.find('.3gp') > -1) and (re.compile('media[a-z0-9]?[a-z0-9]?[a-z0-9]?\.tube8\.com').search(host) or re.compile('mobile[a-z0-9]?[a-z0-9]?[a-z0-9]?\.tube8\.com').search(host)):
                    website_id = 'tube8'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Tvuol.uol.com.br Video file caching is handled here.
            if not matched and o.enable_tvuol_cache:
                if host.find('mais.uol.com.br') > -1 and path.find('.flv') > -1:
                    website_id = 'tvuol'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Blip.tv Video file caching is handled here.
            if not matched and o.enable_bliptv_cache:
                if re.compile('\.video[a-z0-9]?[a-z0-9]?\.blip\.tv').search(host) and (path.find('.flv') > -1 or path.find('.wmv') > -1 or path.find('.mp4') > -1 or path.find('.rm') > -1 or path.find('.ram') > -1 or path.find('.mov') > -1 or path.find('.avi') > -1 or path.find('.m4v') > -1 or path.find('.mp3') > -1):
                    website_id = 'bliptv'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

            # Break.com Video file caching is handled here.
            if not matched and o.enable_break_cache:
                if host.find('video.break.com') > -1 and (path.find('.flv') > -1 or path.find('.mp4')):
                    website_id = 'break'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        video_id = None
                        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url, 'debug' : str(e) } )
                        trace( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )

                    if video_id is not None:
                        new_url = cache_video(client_ip, website_id, url, video_id)

        # Flush the new url to stdout for squid to process
        try:
            sys.stdout.write(new_url + '\n')
            sys.stdout.flush()
            info( { 'code' : 'REPLIED_WITH', 'message' : new_url } )
        except Exception, e:
            warn( { 'code' : WRITEBACK_ERR, 'message' : 'Could not send a reply message to Squid server.', 'debug' : str(e) } )
            trace( { 'code' : WRITEBACK_ERR, 'message' : traceback.format_exc() } )
        input = sys.stdin.readline()
    else:
        info( { 'code' : VIDEOCACHE_EXIT, 'message' : 'Received a stop signal from Squid server. Stopping Videocache.' } )
        exit = True
        # squid_part

def reload():
    global o
    try:
        o = VideocacheOptions('/etc/videocache.conf', root)
    except Exception, e:
        syslog_msg( halt_message + ' Debug: '  + traceback.format_exc().replace('\n', ''))
        sys.exit(1)

    if o.halt:
        syslog_msg(halt_message)
        sys.exit(1)

if __name__ == '__main__':
    # Parse command line options.
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

    info( { 'code' : VIDEOCACHE_START, 'message' : 'Starting Videocache.' } )

    try:
        squid = threading.Thread(target = squid_part)
        video_info = threading.Thread(target = sync_video_info)
        squid.start()
        video_info.start()
        squid.join()
        video_info.join()
        #squid_part()
    except Exception, e:
        error( { 'code' : VIDEOCACHE_RUNTIME_ERR, 'message' : 'Encountered an error while in service.', 'debug' : str(e) } )
        trace( { 'code' : VIDEOCACHE_RUNTIME_ERR, 'message' : traceback.format_exc() } )

