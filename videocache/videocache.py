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
from store import generalized_cached_url, get_generalized_filename
from vcoptions import VideocacheOptions
from vcsysinfo import get_all_info

from optparse import OptionParser

import cookielib
import os
import signal
import sys
import threading
import time
import traceback
import urllib
import urllib2
import urlparse

# Cookie processor and default socket timeout
cj = cookielib.CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)))
socket.setdefaulttimeout(90)

def info(params = {}):
    if o.enable_videocache_log and o.vc_logger:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : LOG_LEVEL_INFO, 'process_id' : process_id})
        o.vc_logger.info(build_message(params))

def error(params = {}):
    if o.enable_videocache_log and o.vc_logger:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : LOG_LEVEL_ERR, 'process_id' : process_id})
        o.vc_logger.error(build_message(params))

def warn(params = {}):
    if o.enable_videocache_log and o.vc_logger:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : LOG_LEVEL_WARN, 'process_id' : process_id})
        o.vc_logger.debug(build_message(params))

def trace(params = {}):
    if o.enable_trace_log and o.trace_logger:
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
    last_ssi_at = now - 21500
    ssi_interval = 21600
    last_ccp_at = now
    ccp_interval = 300
    last_cv_at = now - 1750
    cv_interval = 1800

    wait_time = 120
    sleep_time = 0.05
    while True:
        now = time.time()
        try:
            if (now - last_ssi_at) > ssi_interval:
                last_ssi_at = now
                submit_system_info()
            if (now - last_ccp_at) > ccp_interval:
                last_ccp_at = now
                cleanup_local_cpn_pool(now)
            if (now - last_cv_at) > cv_interval:
                last_cv_at = now
                cleanup_video()
            video = local_video_queue.get(timeout = wait_time)
            try:
                result = VideoQueue.with_timeout(0.5, VideoQueue.first, { 'website_id' : video['website_id'], 'video_id' : video['video_id'], 'format' : video['format'] })
                if result and (result.client_ip != video['client_ip'] or (video['access_time'] - result.access_time) > o.hit_time_threshold):
                    result.update_attributes({ 'client_ip' : video['client_ip'], 'access_time' : video['access_time'], 'access_count' : result.access_count + 1 })
                else:
                    VideoQueue.with_timeout(0.5, VideoQueue.create, video)
            except Exception, e:
                wnt({ 'code' : 'VIDEO_QUEUE_WARN', 'message' : 'Could not queue video info to mysql. Please check if mysql is running. ' + str(video), 'debug' : str(e) })
            time.sleep(sleep_time)
        except Empty, e:
            continue
        except Exception, e:
            ent({ 'code' : 'VIDEO_QUEUE_FAIL', 'message' : 'Could not queue video info to mysql. Please report if you see this error very frequently.', 'debug' : str(e) })
            time.sleep(0.5)

def cleanup_video():
    try:
        delete_video(o)
    except Exception, e:
        wnt({ 'code' : 'SYNC_WARN', 'message' : 'Please report this if it occurs frequently.', 'debug' : str(e) })

def submit_system_info():
    try:
        if o.client_email != '':
            sys_info = { 'id' : o.id, 'email' : eval('o.cl' + 'ie' + 'nt_' + 'em' + 'ail'), 'version' : o.version, 'revision' : o.revision, 'trial' : o.trial }
            sys_info.update(get_all_info(o))
            new_info = {}
            for k,v in sys_info.items():
                new_info['[server][' + k + ']'] = v

            cookie_handler = urllib2.HTTPCookieProcessor()
            redirect_handler = urllib2.HTTPRedirectHandler()
            info_opener = urllib2.build_opener(redirect_handler, cookie_handler)

            info_opener.open(o.info_server, urllib.urlencode(new_info)).read()
        else:
            warn({ 'code' : 'RRE_LIAME_TNEILC'[::-1], 'message' : '.reludehcs-cv tratser ,oslA .diuqS tratser/daoler dna noitpo siht teS .tes ton si fnoc.ehcacoediv/cte/ ni liame_tneilc noitpo ehT'[::-1] })
    except Exception, e:
        wnt({ 'code' : 'SYNC_WARN', 'message' : 'Please report this if it occurs frequently.', 'debug' : str(e) })

def cleanup_local_cpn_pool(now = time.time()):
    global local_cpn_pool
    cut_off_time = now - o.cpn_lifetime
    for cpn_id in local_cpn_pool.keys():
        try:
            if cut_off_time > local_cpn_pool[cpn_id]['last_used']:
                local_cpn_pool.pop(cpn_id, None)
        except:
            pass

def non_ascci_video_id_warning(website_id, video_id, client_ip):
    wnt( { 'code' : 'VIDEO_ID_ENCODING', 'message' : 'Video ID contains non-ascii characters. Will not queue this.', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )

def get_youtube_video_id_from_cpn(cpn, video_id):
    global local_cpn_pool
    if cpn in local_cpn_pool:
        local_cpn_pool[cpn]['last_used'] = time.time()
        return local_cpn_pool[cpn]['video_id']

    if len(video_id) == 11:
        local_cpn_pool[cpn] = { 'video_id' : video_id, 'last_used' : time.time() }
        return video_id

    result = YoutubeCPN.with_timeout(0.2, YoutubeCPN.first, { 'cpn' : cpn })
    if result:
        video_id = result.video_id
        local_cpn_pool[cpn] = { 'video_id' : video_id, 'last_used' : time.time() }
        return video_id

    time.sleep(0.5)
    result = YoutubeCPN.with_timeout(0.2, YoutubeCPN.first, { 'cpn' : cpn })
    if result:
        video_id = result.video_id
        local_cpn_pool[cpn] = { 'video_id' : video_id, 'last_used' : time.time() }
        return video_id
    return video_id

def squid_part():
    global exit, local_cpn_pool, local_video_queue

    started_at = time.time()
    line = sys.stdin.readline()
    while line:
        new_url, url, client_ip, skip, host, path, query, matched = '', '', '-', False, '', '', '', False
        try:
            fields = line.strip().split(' ')
            if len(fields) < 4:
                warn( { 'code' : 'INPUT_WARN', 'message' : 'Input received from Squid is not parsable. Skipping this URL ' + line } )
                skip = True
            elif fields[3].upper() != 'GET':
                warn( { 'code' : 'HTTP_METHOD_WARN', 'message' : 'Cant handle HTTP method ' + fields[3].upper() + '. Skipping this URL.' } )
                skip = True
            else:
                url = fields[0]
                client_ip = fields[1].split('/')[0]
                fragments = urlparse.urlsplit(fields[0])
                if (fragments[0] != 'http' and fragments[0] != 'https') or fragments[1] == '' or fragments[2] == '':
                    warn( { 'code' : 'URL_WARN', 'client_ip' : client_ip, 'message' : 'Cant process. Skipping this URL ' + url } )
                    skip = True
                else:
                    [host, path, query] = [fragments[1], fragments[2], fragments[3]]
        except Exception, e:
            wnt( { 'code' : 'INPUT_PARSE_ERR', 'message' : 'Could not get required informatoin after parsing the input. Skipping this URL ' + line, 'debug' : str(e) } )
            skip = True

        try:
            if o.client_email != '':
                if not skip and o.enable_videocache:
                    for website_id in o.websites:
                        if o.enabled_websites[website_id]:
                            (matched, website_id, video_id, format, search, queue) = eval('check_' + website_id + '_video(o, url, host, path, query)')
                            if matched:
                                if not video_id:
                                    warn( { 'code' : 'URL_ERR', 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )
                                    break

                                info( { 'code' : 'URL_HIT', 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : url } )
                                if not is_ascii(video_id):
                                    non_ascci_video_id_warning(website_id, video_id, client_ip)
                                    break

                                if website_id == 'youtube':
                                    cpn = get_youtube_cpn_from_query_or_path(query, path)
                                    if len(video_id) == 11:
                                        local_cpn_pool[cpn] = { 'video_id' : video_id, 'last_used' : time.time() }

                                if search:
                                    if website_id == 'youtube':
                                        youtube_params = {}
                                        if o.enable_youtube_partial_caching:
                                            youtube_params.update(get_youtube_video_range_from_query_or_path(query, path))
                                            if youtube_params['start'] > 2048 and youtube_params['end'] > 0: youtube_params.update({ 'strict_mode' : True })
                                        (found, filename, dir, size, index, new_url) = youtube_cached_url(o, video_id, website_id, format, youtube_params)
                                        if not found:
                                            old_video_id = video_id
                                            video_id = get_youtube_video_id_from_cpn(cpn, video_id)
                                            if old_video_id != video_id:
                                                (found, filename, dir, size, index, new_url) = youtube_cached_url(o, video_id, website_id, format, youtube_params)
                                    else:
                                        (found, filename, dir, size, index, new_url) = eval(website_id + '_cached_url(o, video_id, website_id, format)')
                                    if new_url == '':
                                        info({ 'code' : 'CACHE_MISS', 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' })
                                    else:
                                        info({ 'code' : 'CACHE_HIT', 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + new_url })
                                        VideoFile.with_timeout(0.2, VideoFile.create, { 'cache_dir' : dir, 'website_id' : website_id, 'filename' : filename, 'size' : size, 'access_time' : current_time() })

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
                                            warn({ 'code' : 'PLUGIN_QUEUE_FULL', 'message' : 'You are reaching ' + str(o.max_queue_size_per_plugin) + ' requests (for uncached new videos) per minute per plugin on your server. Try to increase the url_rewrite_children in squid.conf. If that doesnt fix this warning, please contact us.' })
                                            local_video_queue = Queue(o.max_queue_size_per_plugin)
                                        local_video_queue.put(params)
                                break
            else:
                warn( { 'code' : 'RRE_LIAME_TNEILC'[::-1], 'message' : '.reludehcs-cv tratser ,oslA .diuqS tratser/daoler dna noitpo siht teS .tes ton si fnoc.ehcacoediv/cte/ ni liame_tneilc noitpo ehT'[::-1] } )
        except Exception, e:
            wnt({ 'code' : 'VIDEOCACHE_UNKNOWN_ISSUE', 'message' : 'Unknown issue detected with videocache. Please report if you see this frequently.', 'debug' : str(e) })

        try:
            sys.stdout.write(new_url + '\n')
            sys.stdout.flush()
        except Exception, e:
            wnt( { 'code' : 'WRITEBACK_ERR', 'message' : 'Could not send a reply message to Squid server.', 'debug' : str(e) } )
        line = sys.stdin.readline()
    else:
        info( { 'code' : 'VIDEOCACHE_EXIT', 'message' : 'Received a stop signal from Squid server. Stopping Videocache.' } )
        exit = True
        os.kill(os.getpid(), signal.SIGTERM)

if __name__ == '__main__':
    parser = OptionParser()
    options, args = parser.parse_args()

    halt_message = 'One or more errors while starting Videocache. Please check syslog and videocache log for errors.'
    try:
        o = VideocacheOptions('/etc/videocache.conf')
        o.set_loggers()
    except Exception, e:
        syslog_msg( halt_message + ' Debug: '  + traceback.format_exc().replace('\n', ''))
        sys.exit(1)

    if o.halt:
        syslog_msg(halt_message)
        sys.exit(1)

    local_video_queue = Queue(o.max_queue_size_per_plugin)
    local_cpn_pool = {}
    process_id = os.getpid()
    exit = False
    initialize_database(o)

    if o.cache_host == '':
        error( { 'code' : 'CACHE_HOST_ERR', 'message' : 'The option cache_host in /etc/videocache.conf is not set. Please set it and restart/reload Squid daemon. Videocache will be disabled until you set cache_host.' } )
        o.enable_videocache = 0
    elif o.cache_host.find('127.0.0.1') > -1:
        warn( { 'code' : 'CACHE_HOST_WARN', 'message' : 'The option cache_host is set to 127.0.0.1. Videocache will be able to serve videos only to localhost. Please set it to the private/public IP address of the server and restart/reload Squid daemon' } )

    info( { 'code' : 'VIDEOCACHE_START', 'message' : 'Starting Videocache.' } )

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
        ent( { 'code' : 'VIDEOCACHE_RUNTIME_ERR', 'message' : 'Encountered an error while in service.', 'debug' : str(e) } )

