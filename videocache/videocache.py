#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from vcredis import VideoFile, VideoQueue, AccessLogQueue
from common import *
from store import generalized_cached_url, get_generalized_filename
from vcoptions import VideocacheOptions

import os
import sys
import traceback
import urlparse

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

def non_ascci_video_id_warning(website_id, video_id, client_ip):
    wnt( { 'code' : 'VIDEO_ID_ENCODING', 'message' : 'Video ID contains non-ascii characters. Will not queue this.', 'debug' : str(e), 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id } )

def write_back(new_url = '', request_id = ''):
    try:
        sys.stdout.write(request_id + new_url + '\n')
        sys.stdout.flush()
    except Exception, e:
        wnt( { 'code' : 'WRITEBACK_ERR', 'message' : 'Could not send a reply message to Squid server.', 'debug' : str(e) } )

def squid_part():
    global video_queue, video_file, access_log_queue

    concurrent = None
    request_id = ''

    line = sys.stdin.readline()
    while line:
        new_url, url, client_ip, skip, host, path, query, matched = '', '', '-', False, '', '', '', False
        try:
            line = line.strip()
            fields = line.split(' ')
            if len(fields) < 4:
                warn( { 'code' : 'INPUT_WARN', 'message' : 'Input received from Squid is not parsable. Skipping this URL ' + line } )
                skip = True
            elif not ('GET' in fields or 'get' in fields):
                warn( { 'code' : 'HTTP_METHOD_WARN', 'message' : 'Cant handle this HTTP method' + '. Skipping this URL. ' + line } )
                skip = True
            else:
                if concurrent == None:
                    if is_integer(fields[0]):
                        concurrent = True
                    else:
                        concurrent = False
                if concurrent:
                    if len(fields) < 5:
                        warn( { 'code' : 'INPUT_WARN', 'message' : 'Input received from Squid is not parsable. Skipping this URL ' + line } )
                        skip = True
                    else:
                        request_id = fields[0] + ' '
                        url = fields[1]
                        client_ip = fields[2].split('/')[0]
                        fragments = urlparse.urlsplit(url)
                        if (fragments[0] != 'http' and fragments[0] != 'https') or fragments[1] == '' or fragments[2] == '':
                            warn( { 'code' : 'URL_WARN', 'client_ip' : client_ip, 'message' : 'Cant process. Skipping this URL ' + url } )
                            skip = True
                        else:
                            [host, path, query] = [fragments[1], fragments[2], fragments[3]]
                else:
                    request_id = ''
                    url = fields[0]
                    client_ip = fields[1].split('/')[0]
                    fragments = urlparse.urlsplit(url)
                    if (fragments[0] != 'http' and fragments[0] != 'https') or fragments[1] == '' or fragments[2] == '':
                        warn( { 'code' : 'URL_WARN', 'client_ip' : client_ip, 'message' : 'Cant process. Skipping this URL ' + url } )
                        skip = True
                    else:
                        [host, path, query] = [fragments[1], fragments[2], fragments[3]]
        except Exception, e:
            wnt( { 'code' : 'INPUT_PARSE_ERR', 'message' : 'Could not get required informatoin after parsing the input. Skipping this URL ' + line, 'debug' : str(e) } )
            skip = True

        if not o.client_email:
            warn( { 'code' : 'RRE_LIAME_TNEILC'[::-1], 'message' : '.reludehcs-cv tratser ,oslA .diuqS tratser/daoler dna noitpo siht teS .tes ton si fnoc.ehcacoediv/cte/ ni liame_tneilc noitpo ehT'[::-1] } )

        if skip or not o.client_email or not o.enable_videocache:
            write_back(new_url, request_id)
            line = sys.stdin.readline()
            continue

        try:
            for website_id in o.enabled_website_keys:
                (matched, website_id, video_id, fmt, search, queue, report_hit) = eval('check_' + website_id + '_video(o, url, host, path, query)')
                if matched:
                    if not video_id:
                        warn( { 'code' : 'URL_ERR', 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not find Video ID in URL ' + url } )
                        break

                    if report_hit: info( { 'code' : 'URL_HIT', 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : url } )
                    if not is_ascii(video_id):
                        non_ascci_video_id_warning(website_id, video_id, client_ip)
                        break

                    if search:
                        (found, filename, cache_dir, size, index, new_url) = eval(website_id + '_cached_url(o, video_id, website_id, fmt)')

                        if new_url == '':
                            info({ 'code' : 'CACHE_MISS', 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'message' : 'Requested video was not found in cache.' })
                            if queue:
                                queue_url = url
                                shall_queue = True
                                if website_id == 'android':
                                    shall_queue = False

                                if shall_queue:
                                    video_queue.add_info(website_id, video_id, fmt, queue_url)
                            if search:
                                access_log_queue.push(url)
                        else:
                            info({ 'code' : 'CACHE_HIT', 'website_id' : website_id, 'client_ip' : client_ip, 'video_id' : video_id, 'size' : size, 'message' : 'Video was served from cache using the URL ' + request_id + new_url })
                            video_file.increment_score(cache_dir, website_id, filename)
                    break
        except Exception, e:
            wnt({ 'code' : 'VIDEOCACHE_UNKNOWN_ISSUE', 'message' : 'Unknown issue detected with videocache. Please report if you see this frequently.', 'debug' : str(e) })

        write_back(new_url, request_id)
        line = sys.stdin.readline()
    else:
        info( { 'code' : 'VIDEOCACHE_EXIT', 'message' : 'Received a stop signal from Squid server. Stopping Videocache.' } )
        return

if __name__ == '__main__':
    halt_message = 'One or more errors while starting Videocache. Please check syslog and videocache log for errors.'
    try:
        o = VideocacheOptions('/etc/videocache.conf')
        o.set_loggers()
        video_file = VideoFile(o)
        video_queue = VideoQueue(o)
        access_log_queue = AccessLogQueue(o)
    except Exception, e:
        syslog_msg( halt_message + ' Debug: '  + traceback.format_exc().replace('\n', ''))
        sys.exit(1)

    if o.halt:
        syslog_msg(halt_message)
        sys.exit(1)

    process_id = os.getpid()

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
        squid_part()
    except Exception, e:
        ent( { 'code' : 'VIDEOCACHE_RUNTIME_ERR', 'message' : 'Encountered an error while in service.', 'debug' : str(e) } )

