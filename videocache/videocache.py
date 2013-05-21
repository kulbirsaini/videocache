#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from Queue import Queue, Empty

from database import initialize_database, VideoFile, VideoQueue, YoutubeCPN
from common import *
from error_codes import *
from store import generalized_cached_url, get_generalized_filename
from vcoptions import VideocacheOptions
from vcsysinfo import *

from optparse import OptionParser
from xmlrpclib import ServerProxy

import cgi
import logging
import logging.handlers
import os
import re
import signal
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

def ent(params = {}):
    error(params)
    params.update({ 'message' : traceback.format_exc() })
    trace(params)

def wnt(params = {}):
    error(params)
    params.update({ 'message' : traceback.format_exc() })
    trace(params)

def sync_video_info():
    global local_video_queue
    now = time.time()
    sysinfo_last_submitted_at = now - 3540
    sysinfo_submit_interval = 3600
    cleanup_cpn_pool_last_at = now
    cleanup_cpn_pool_interval = 300

    wait_time = 120
    sleep_time = 0.05
    while True:
        try:
            if (now - sysinfo_last_submitted_at) > sysinfo_submit_interval:
                sysinfo_last_submitted_at = now
                submit_system_info()
            if (now - cleanup_cpn_pool_last_at) > cleanup_cpn_pool_interval:
                cleanup_local_cpn_pool(now)
            video = local_video_queue.get(timeout = wait_time)
            try:
                result = VideoQueue.first({ 'website_id' : video['website_id'], 'video_id' : video['video_id'], 'format' : video['format'] })
                if result and (result.client_ip != video['client_ip'] or (video['access_time'] - result.access_time) > o.hit_time_threshold):
                    result.update_attributes({ 'client_ip' : video['client_ip'], 'access_time' : video['access_time'], 'access_count' : result.access_count + 1 })
                else:
                    VideoQueue.create(video)
            except Exception, e:
                wnt({ 'code' : 'VIDEO_SUBMIT_WARN', 'message' : 'Could not submit video information to mysql. Please check if mysql is still running. ' + str(video), 'debug' : str(e) })
            time.sleep(sleep_time)
        except Empty, e:
            continue
        except Exception, e:
            ent({ 'code' : 'VIDEO_SUBMIT_FAIL', 'message' : 'Could not submit video information to mysql. Please report if you see this error very frequently.', 'debug' : str(e) })
        now = time.time()

def submit_system_info():
    delete_video(o)
    try:
        num_tries = 0
        while num_tries < 5:
            try:
                video_pool.ping()
                sys_info = { 'id' : o.id, 'email' : eval('o.cl' + 'ie' + 'nt_' + 'em' + 'ail'), 'version' : o.version, 'revision' : o.revision }
                sys_info.update(get_all_info(o))
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

def cleanup_local_cpn_pool(now = time.time()):
    global local_cpn_pool
    cut_off_time = now - o.cpn_lifetime
    for cpn_id in local_cpn_pool.keys():
        try:
            if cut_off_time > local_cpn_pool[cpn_id]['last_used']:
                local_cpn_pool.pop(cpn_id, None)
        except:
            pass

def connection():
    global video_pool
    try:
        video_pool.ping()
    except Exception, e:
        try:
            video_pool = ServerProxy(o.rpc_url)
            video_pool.ping()
        except Exception, e:
            ent({ 'code' : RPC_CONNECT_ERR, 'message' : 'Could not connect to RPC server (videocache scheduler) at ' + o.rpc_host + ':' + str(o.rpc_port) + '. Please check scheduler status. If needed, restart scheduler using \'vc-scheduler -s restart\' command.', 'debug' : str(e)})

def non_ascci_video_id_warning(website_id, video_id, client_ip):
    wnt( { 'code' : VIDEO_ID_ENCODING, 'message' : 'Video ID contains non-ascii characters. Will not queue this.', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )

def squid_part():
    global exit, local_cpn_pool, local_video_queue

    input = sys.stdin.readline()
    while input:
        new_url, url, client_ip, skip, host, path, query, matched = '', '', '-', False, '', '', '', False
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
            wnt( { 'code' : INPUT_PARSE_ERR, 'message' : 'Could not get required informatoin after parsing the input. Skipping this URL.', 'debug' : str(e) } )
            skip = True

        if o.client_email != '':
            if not skip and o.enable_videocache:
                for website_id in o.websites:
                    if eval('o.enable_' + website_id + '_cache'):
                        (matched, website_id, video_id, format, search, queue) = eval('check_' + website_id + '_video(o, url, host, path, query)')
                        if matched:
                            if not video_id:
                                warn( { 'code' : URL_ERR, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )
                                break

                            info( { 'code' : URL_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : url } )
                            if not is_ascii(video_id):
                                non_ascci_video_id_warning(website_id, video_id, client_ip)
                                break

                            if search:
                                if website_id == 'youtube':
                                    youtube_params = {}
                                    if o.enable_youtube_partial_caching:
                                        youtube_params.update(get_youtube_video_range_from_query(query))
                                        if youtube_params['start'] > 2048 and youtube_params['end'] > 0: youtube_params.update({ 'strict_mode' : True })
                                    (found, filename, dir, size, index, new_url) = youtube_cached_url(o, video_id, website_id, format, youtube_params)
                                    if not found:
                                        cpn = get_youtube_cpn_from_query(query)
                                        if len(video_id) == 11:
                                            if cpn not in local_cpn_pool:
                                                local_cpn_pool[cpn] = { 'video_id' : video_id, 'last_used' : time.time() }
                                        else:
                                            old_video_id = video_id
                                            try:
                                                if cpn in local_cpn_pool:
                                                    video_id = local_cpn_pool[cpn]['video_id']
                                                    local_cpn_pool[cpn]['last_used'] = time.time()
                                                else:
                                                    result = YoutubeCPN.first({ 'cpn' : cpn })
                                                    if result:
                                                        video_id = result.video_id
                                                    else:
                                                        video_id = False
                                                    if video_id == False:
                                                        time.sleep(2)
                                                        result = YoutubeCPN.first({ 'cpn' : cpn })
                                                        if result:
                                                            video_id = result.video_id
                                                        else:
                                                            video_id = False
                                                if video_id:
                                                    if cpn not in local_cpn_pool:
                                                        local_cpn_pool[cpn] = { 'video_id' : video_id, 'last_used' : time.time() }
                                                    (found, filename, dir, size, index, new_url) = youtube_cached_url(o, video_id, website_id, format, youtube_params)
                                                else:
                                                    video_id = old_video_id
                                            except Exception, e:
                                                video_id = old_video_id
                                else:
                                    (found, filename, dir, size, index, new_url) = eval(website_id + '_cached_url(o, video_id, website_id, format)')
                                if new_url == '':
                                    info({ 'code' : CACHE_MISS, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' })
                                else:
                                    info({ 'code' : CACHE_HIT, 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url })
                                    VideoFile.create({ 'cache_dir' : dir, 'website_id' : website_id, 'filename' : filename, 'size' : size, 'access_time' : current_time() })

                            if new_url == '' and queue and video_id:
                                params = {'video_id' : video_id, 'client_ip' : client_ip, 'url' : url, 'website_id' : website_id, 'access_time' : time.time(), 'first_access' : time.time(), 'format' : format}
                                shall_queue = False
                                if website_id == 'youtube':
                                    params.update({ 'url' : ''})
                                    if len(video_id) == 11:
                                        shall_queue = True
                                elif website_id != 'android':
                                    shall_queue = True
                                    local_video_queue.put(params)
                                if shall_queue:
                                    if local_video_queue.full():
                                        warn({ 'code' : 'LOCAL_QUEUE_FULL', 'message' : 'You are reaching ' + str(o.max_queue_size_per_plugin) + ' requests (for uncached new videos) per minute per plugin on your server. Try to increase the url_rewrite_children in squid.conf. If that doesnt fix this warning, please contact us.' })
                                        try:
                                            local_video_queue.get()
                                        except:
                                            pass
                                    local_video_queue.put(params)
                            break
        else:
            warn( { 'code' : 'RRE_LIAME_TNEILC'[::-1], 'message' : '.reludehcs-cv tratser ,oslA .diuqS tratser/daoler dna noitpo siht teS .tes ton si fnoc.ehcacoediv/cte/ ni liame_tneilc noitpo ehT'[::-1] } )

        try:
            sys.stdout.write(new_url + '\n')
            sys.stdout.flush()
        except Exception, e:
            wnt( { 'code' : WRITEBACK_ERR, 'message' : 'Could not send a reply message to Squid server.', 'debug' : str(e) } )
        input = sys.stdin.readline()
    else:
        info( { 'code' : VIDEOCACHE_EXIT, 'message' : 'Received a stop signal from Squid server. Stopping Videocache.' } )
        exit = True
        os.kill(os.getpid(), signal.SIGTERM)

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

    local_video_queue = Queue(o.max_queue_size_per_plugin)
    local_cpn_pool = {}
    video_pool = None
    process_id = os.getpid()
    exit = False
    initialize_database(o)

    if o.cache_host == '':
        error( { 'code' : CACHE_HOST_ERR, 'message' : 'The option cache_host in /etc/videocache.conf is not set. Please set it and restart/reload Squid daemon. Videocache will be disabled until you set cache_host.' } )
        o.enable_videocache = 0
    elif o.cache_host.find('127.0.0.1') > -1:
        warn( { 'code' : CACHE_HOST_WARN, 'message' : 'The option cache_host is set to 127.0.0.1. Videocache will be able to serve videos only to localhost. Please set it to the private/public IP address of the server and restart/reload Squid daemon' } )

    info( { 'code' : VIDEOCACHE_START, 'message' : 'Starting Videocache.' } )

    # Import website functions
    for website_id in o.websites:
        exec(website_id + '_cached_url = generalized_cached_url')
        exec('from websites.' + website_id + ' import *')

    try:
        squid = threading.Thread(target = squid_part)
        video_info = threading.Thread(target = sync_video_info)
        squid.start()
        video_info.start()
        squid.join()
        video_info.join()
    except Exception, e:
        ent( { 'code' : VIDEOCACHE_RUNTIME_ERR, 'message' : 'Encountered an error while in service.', 'debug' : str(e) } )

