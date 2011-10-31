#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
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

def get_cached_url(website_id, video_id, format, client_ip = '-'):
    for dir in o.base_dirs[website_id]:
        video_path = os.path.join(dir, video_id) + format
        if os.path.isfile(video_path):
            try:
                size = os.path.getsize(video_path)
            except:
                size = '-'

            try:
                os.utime(video_path, None)
                if len(o.base_dirs[website_id]) > 1:
                    index = o.base_dirs[website_id].index(dir)
                else:
                    index = ''
                cached_url = os.path.join(o.cache_url, 'videocache', str(index), website_id)
                url = os.path.join(cached_url, urllib.quote(video_id)) + format
                new_url = o.redirect_code + ':' + refine_url(url, ['noflv'])
                info( { 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url } )
                return new_url
            except Exception, e:
                warn( { 'code' : VIDEO_SEARCH_WARN, 'message' : 'Could not search video in local cache directory ' + video_path + ' .', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )
                trace( { 'code' : VIDEO_SEARCH_WARN, 'message' : traceback.format_exc(), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )

    info( { 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' } )
    return ''

def non_ascci_video_id_warning(website_id, video_id, client_ip):
    warn( { 'code' : VIDEO_ID_ENCODING, 'message' : 'Video ID contains non-ascii characters. Will not queue this.', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )
    trace( { 'code' : VIDEO_ID_ENCODING, 'message' : traceback.format_exc(), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )

def search_and_queue(params):
    client_ip = params.get('client_ip', '-')
    website_id = params.get('website_id', '-')
    url = params.get('url', None)
    video_id = params.get('video_id', None)
    format = params.get('format', '')
    queue = params.get('queue', True)
    search = params.get('search', True)
    cached_url = ''

    if video_id is None:
        warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )
        return cached_url

    info( { 'code' : URL_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : url } )
    if not is_ascii(video_id):
        non_ascci_video_id_warning(website_id, video_id, client_ip)
        return cached_url

    video_id = urllib.unquote(video_id)
    if search:
        cached_url = get_cached_url(website_id, video_id, format, client_ip)

    if cached_url == '' and queue:
        add_video_to_local_pool(video_id, {'video_id' : video_id, 'client_ip' : client_ip, 'urls' : [url], 'website_id' : website_id, 'access_time' : time.time(), 'format' : format})
    return cached_url

def squid_part():
    # Import website functions
    for website in o.websites:
        exec('from websites.' + website + ' import *')

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

                for website in o.websites:
                    if eval('o.enable_' + website + '_cache'):
                        (matched, website_id, video_id, format, search, queue) = eval('check_' + website + '_video(url, host, path, query)')
                        if matched:
                            new_url = search_and_queue({ 'website_id' : website_id, 'video_id' : video_id, 'url' : url, 'format' : format, 'client_ip' : client_ip, 'search' : search, 'queue' : queue })
                            break
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

