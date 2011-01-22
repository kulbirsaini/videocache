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
from vcdaemon import VideocacheDaemon
from vcoptions import VideocacheOptions

from optparse import OptionParser
from SimpleXMLRPCServer import SimpleXMLRPCServer
from xmlrpclib import ServerProxy

import cookielib
import logging
import pwd
import socket
import statvfs
import sys
import threading
import time
import traceback
import urllib2
import urlparse

# Cookie processor and default socket timeout
cj = cookielib.CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)))
socket.setdefaulttimeout(90)

def info(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.INFO), 'process_id' : process_id })
    o.vcs_logger.info(build_message(params))

def error(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.ERROR), 'process_id' : process_id })
    o.vcs_logger.error(build_message(params))

def warn(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.WARN), 'process_id' : process_id })
    o.vcs_logger.debug(build_message(params))

def trace(params = {}):
    params.update({ 'trace_logformat' : o.trace_logformat, 'timeformat' : o.timeformat, 'process_id' : process_id })
    o.trace_logger.info(build_trace(params))

def connection():
    global video_pool
    try:
        video_pool = ServerProxy('http://' + o.rpc_host + ':' + str(o.rpc_port))
        info({ 'code' : RPC_CONNECT, 'message' : 'Connected to RPC server.'})
    except Exception, e:
        error({ 'code' : RPC_CONNECT_ERR, 'message' : 'Could not connect to RPC server.', 'debug' : str(e)})
        trace({ 'code' : RPC_CONNECT_ERR, 'message' : traceback.format_exc() })

class VideoPool:
    """
    This class is for sharing the current packages being downloading
    across various instances of Videocache via RPC.
    """
    scores = {}
    queue = {}
    active = {}
    time_threshold = 15

    def __init__(self):
        pass

    def ping(self):
        return True

    def get_active_videos(self):
        return self.active.keys()

    def get_video_scores(self):
        return self.scores

    def get_video_queue(self):
        return self.queue

    def add_videos(self, videos = {}):
        """
        New videos are added to the queue and there scores are set to 0.
        If a video is already queued, its score is incremented by 1.
        """
        info( { 'code' : VIDEOS_RECEIVED, 'message' : 'Received ' + str(len(videos)) + ' videos from Videocache.' } )
        for video_id in videos:
            for params in videos[video_id]:
                self.add_video(video_id, params)
        return True

    def add_video(self, video_id, params):
        if video_id not in self.queue:
            self.queue[video_id] = params
            self.scores[video_id] = 1
        else:
            old_data = self.queue[video_id]
            try:
                if params['client_ip'] == old_data['client_ip'] and (int(params['access_time']) - int(old_data['access_time'])) > self.time_threshold:
                    self.inc_score(video_id)
                    self.queue[video_id].update( { 'access_time' : params['access_time'] } )
            except Exception, e:
                self.inc_score(video_id)

            #try:
            #    self.queue[video_id].update( { 'urls' : list(set(old_data['urls'] + params['urls'])) } )
            #except Exception, e:
            #    pass
        return True

    def get_score(self, video_id):
        """Get the score of video represented by video_id."""
        if video_id in self.scores:
            return self.scores[video_id]
        else:
            return 0

    def set_score(self, video_id, score = 1):
        """Set the priority score of a video_id."""
        if video_id in self.scores:
            self.scores[video_id] = score
        return True

    def inc_score(self, video_id, incr = 1):
        """Increase the priority score of video represented by video_id."""
        if video_id in self.scores:
            self.scores[video_id] += incr
        return True

    def dec_score(self, video_id, decr = 1):
        """Decrease the priority score of video represented by video_id."""
        if video_id in self.scores:
            self.scores[video_id] -= decr
    def get_popular(self):
        """Return the video_id of the most frequently access video."""
        vk = [(v,k) for k,v in self.scores.items()]
        if len(vk) != 0:
            video_id = sorted(vk, reverse=True)[0][1]
            return video_id
        return False

    def get_details(self, video_id):
        """Return the details of a particular video represented by video_id."""
        if video_id in self.queue.keys():
            return self.queue[video_id]
        return False

    def remove_from_queue(self, video_id):
        """Dequeue a video_id from the download queue."""
        if video_id in self.queue:
            self.queue.pop(video_id)
        if video_id in self.scores:
            self.scores.pop(video_id)
        return True

    def remove_url_from_queue(self, video_id, url):
        """Dequeue a url for a video_id from the download queue."""
        if video_id in self.queue:
            if url in self.queue[video_id]['urls']:
                self.queue[video_id]['urls'].remove(url)
        return True

    def remove(self, video_id):
        """Remove video_id from queue as well as active connection list."""
        return self.remove_from_queue(video_id) and self.remove_conn(video_id)

    def remove_url(self, video_id, url):
        """Remove url from url list for a video_id."""
        if len(self.queue[video_id]['urls']) == 1:
            return self.remove(video_id)
        else:
            return self.remove_url_from_queue(video_id, url)

    def flush(self):
        """Flush the queue and reinitialize everything."""
        self.queue = {}
        self.scores = {}
        self.active = {}
        return True

    def start_cache_thread(self, video_id, params):
        """Start a new thread which will cache the vdieo"""
        new_thread = threading.Thread(target = cache, name = str(video_id), kwargs = { 'params' : params })
        self.set_score(video_id, 0)
        self.add_conn(video_id, new_thread)
        new_thread.start()
        info( { 'code' : CACHE_THREAD_START, 'website_id' : params['website_id'], 'video_id' : params['video_id'], 'message' : 'Starting cache thread.' } )
        return True

    def clean_threads(self):
        """Cleanup threads which have exitted."""
        for (video_id, thread) in self.active.items():
            try:
                if not thread.isAlive():
                    self.remove(video_id)
                    info( { 'code' : CACHE_THREAD_REMOVE, 'video_id' : video_id, 'message' : 'Cache thread completed. Removing from active list.' } )
            except Exception, e:
                error( { 'code' : CACHE_THREAD_REMOVE_ERR, 'message' : 'Unable to remove cache thread from thread list', 'debug' : str(e), 'video_id' : video_id } )
                trace( { 'code' : CACHE_THREAD_REMOVE_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id } )
        return True

    def schedule(self):
        """Returns the parameters for a video to be downloaded from remote."""
        try:
            self.clean_threads()
            if o.offline_mode:
                return False
            if self.get_conn_number() < o.max_cache_processes:
                video_id = self.get_popular()
                if video_id != False and self.is_active(video_id) == False and self.get_score(video_id) >= o.hit_threshold:
                    params = self.get_details(video_id)
                    if params != False:
                        self.start_cache_thread(video_id, params)
                        return True
                elif self.is_active(video_id) == True:
                    self.set_score(video_id, 0)
                    return False
        except Exception, e:
            error( { 'code' : VIDEO_SCHEDULE_ERR, 'message' : 'Could not find out the next video to schedule.', 'debug' : str(e) } )
            trace( { 'code' : VIDEO_SCHEDULE_ERR, 'message' : traceback.format_exc() } )
            return False
        return False

    # Functions related download scheduling.
    # Have to mess up things in single class because python
    # RPCServer doesn't allow to register multiple instances.
    def add_conn(self, video_id, thread):
        """Add video_id to active connections list."""
        if video_id not in self.active:
            self.active[video_id] = thread
        return True

    def get_conn_number(self):
        """Return the number of currently active connections."""
        return len(self.active)

    def is_active(self, video_id):
        """Returns whether a connection is active or not."""
        return video_id in self.active

    def remove_conn(self, video_id):
        """Remove video_id from active connections list."""
        if video_id in self.active:
            self.active.pop(video_id)
        return True

class VideoPoolRPCServer(SimpleXMLRPCServer):

    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        self.finished = False
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    def shutdown(self):
        self.finished = True

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def serve_forever(self):
        while not self.finished:
            self.handle_request()

#class VideoPoolDaemon(VideocacheDaemon):
#
#    def __init__(self, o = None, **kwargs):
#        self.o = o
#        VideocacheDaemon.__init__(self, o.scheduler_pidfile, **kwargs)
#
#    def run(self):
#        try:
#            self.o.set_loggers()
#            server = ThreadedServer(VideoPool, hostname = self.o.rpc_host, port = self.o.rpc_port)
#            info( { 'code' : VIDEO_POOL_SERVER_START, 'message' : 'Starting VideoPool Server at port ' + str(self.o.rpc_port) + '.' } )
#            server.start()
#        except Exception, e:
#            error( { 'code' : VIDEO_POOL_SERVER_START_ERR, 'message' : 'Error while starting VideoPool server at port ' + str(self.o.rpc_port) + '.' } )
#            trace( { 'code' : VIDEO_POOL_SERVER_START_ERR, 'message' : traceback.format_exc() } )
#            sys.stdout.write(traceback.format_exc())

def cache(params):
    """This function caches the remote file."""
    client_ip = params.get('client_ip', '-')
    video_id = params.get('video_id', '-')
    website_id = params.get('website_id', '-')
    urls = params.get('urls', [])
    try:
        if video_id == '-' or website_id == '-' or len(urls) == 0:
            error( { 'code' : VIDEO_INFO_ERR, 'message' : 'Enough video information was not available in cache thread.', 'website_id' : website_id, 'video_id' : video_id, 'client_ip' : client_ip } )
            return

        available_dirs = []
        for (dir, tmp_dir) in zip(o.base_dirs[website_id], o.base_dirs['tmp']):
            if os.path.isfile(os.path.join(dir, video_id)):
                info({ 'code' : VIDEO_EXISTS, 'message' : 'Video already exists in one of the cache directories.', 'website_id' : website_id, 'video_id' : video_id, 'client_ip' : client_ip })
                return

            cache_dir = dir.replace(eval('o.' + website_id + '_cache_dir'), '')

            # Check the disk space left in the partition with cache directory.
            disk_stat = os.statvfs(dir)
            disk_available = disk_stat[statvfs.F_BSIZE] * disk_stat[statvfs.F_BAVAIL] / (1024*1024.0)

            # If disk availability reached disk_avail_threshold, then we can't use this cache dir anymore.
            if disk_available < o.disk_avail_threshold:
                warn({'code' : CACHE_DIR_FULL, 'message' : 'Cache directory \'' + cache_dir  + '\' has reached the disk availability threshold. Please check.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip})
                continue
            else:
                available_dirs.append( { 'cache_dir' : dir, 'tmp' : tmp_dir, 'space' : disk_available } )

        if len(available_dirs) == 0:
            error({'code' : CACHE_DIR_ERR, 'message' : 'Could not determine a cache directory to cache the video. Please check.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip})
            return

        params.update( { 'dirs' : available_dirs } )
        eval('cache_' + website_id + '_video(params)')
        return
    except Exception, e:
        error( {'code' : CACHE_THREAD_ERR, 'message' : 'Error in cache thread.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip} )
        trace( {'code' : CACHE_THREAD_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip} )

def cache_remote_url(remote_url, target_file, params = {}):
    info( { 'code' : 'REMOTE_URL_DEBUGGING', 'message' : remote_url } )

    client_ip = params.get('client_ip', '-')
    video_id = params.get('video_id', '-')
    website_id = params.get('website_id', '-')

    if o.proxy:
        urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler( { 'http' : o.proxy, 'https' : o.proxy, 'ftp' : o.proxy } )))
    request = urllib2.Request(remote_url, None, o.std_headers)

    try:
        connection = urllib2.urlopen(request)
        try:
            conn_info = connection.info()
            video_size = int(conn_info.get('content-length', -1))
            if video_size == -1:
                info( { 'code' : VIDEO_SIZE_NOT_SUPPLIED, 'message' : 'Video size was not supplied by the remote server.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            elif o.max_video_size != 0 and o.min_video_size != 0:
                if video_size > o.max_video_size:
                    info( { 'code' : VIDEO_TOO_LARGE, 'message' : 'Video size is large than the specified max video size allowed. Skipping.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
                    return False
                if video_size < o.min_video_size:
                    info( { 'code' : VIDEO_TOO_SMALL, 'message' : 'Video size is smaller than the specified min video size allowed. Skipping.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
                    return False
        except Exception, e:
            warn( { 'code' : CONNECTION_INFO_ERR, 'message' : 'Error while getting connection information.', 'debug' : str(e), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            trace( { 'code' : CONNECTION_INFO_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )

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
            error( { 'code' : CACHE_HTTP_ERR, 'message' : 'HTTP error : ' + str(e.code) + '. An error occured while caching the video at '  + remote_url + '.', 'debug' : str(e), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            trace( { 'code' : CACHE_HTTP_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            return False
        except:
            error( { 'code' : CACHE_HTTP_ERR, 'message' : 'HTTP error. An error occured while caching the video at '  + remote_url + '.', 'debug' : str(e), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            trace( { 'code' : CACHE_HTTP_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            return False
    except Exception, e:
        error( { 'code' : CACHE_ERR, 'message' : 'Could not cache the video at ' + remote_url + '.', 'debug' : str(e), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
        trace( { 'code' : CACHE_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
        return False
    return True

def cache_youtube_video(params):
    mode = 0644
    client_ip = params.get('client_ip', '-')
    video_id = params.get('video_id', '-')
    website_id = params.get('website_id', '-')
    urls = params.get('urls', [])
    dirs = params.get('dirs', [])

    if video_id == '-' or website_id == '-' or len(dirs) == 0 or len(urls) == 0:
        error( { 'code' : VIDEO_INFO2_ERR, 'message' : 'Enough video information was not available in cache thread.', 'website_id' : website_id, 'video_id' : video_id, 'client_ip' : client_ip } )
        return

    if o.proxy:
        urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler( { 'http' : o.proxy, 'https' : o.proxy, 'ftp' : o.proxy } )))
    request = urllib2.Request('http://www.youtube.com/watch?v=%s&gl=US&hl=en' % video_id, None, o.std_headers)
    try:
        webpage = urllib2.urlopen(request).read()
    except Exception, e:
        error( { 'code' : VIDEO_PAGE_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Error while fetching video webpage.', 'debug' : str(e) } )
        trace( { 'code' : VIDEO_PAGE_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )
        return

    for el in ['&el=detailpage', '&el=embedded', '&el=vevo', '']:
        info_url = 'http://www.youtube.com/get_video_info?&video_id=%s%s&ps=default&eurl=&gl=US&hl=en' % (video_id, el)
        request = urllib2.Request(info_url, None, o.std_headers)
        try:
            info_page = urllib2.urlopen(request).read()
            video_info = urlparse.parse_qs(info_page)
            if 'fmt_url_map' in video_info:
                break
        except Exception, e:
            error({'code' : VIDEO_INFO_FETCH_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Error occured while fetching video info..', 'debug' : str(e) } )
            trace( { 'code' : VIDEO_INFO_FETCH_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )
            return

    alternate_ids = []
    video_url = None
    try:
        if 'fmt_url_map' in video_info:
            alternate_urls = [ u.split('|')[1] for u in video_info['fmt_url_map'][0].split(',') ]
            video_url = alternate_urls[0]
            for url in alternate_urls:
                vid = get_youtube_video_id(url)
                if vid and vid not in alternate_ids:
                    alternate_ids.append(vid)
    except Exception, e:
        error( { 'code' : ALTERNATE_VIDEO_ID_ERROR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Error while extracting alternate video id.', 'debug' : str(e) } )
        trace( { 'code' : ALTERNATE_VIDEO_ID_ERROR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )


    if not video_url:
        error( { 'code' : VIDEO_URL_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not determine video URL.' } )
        return

    dir = dirs[0]

    cache_dir = dir['cache_dir']
    tmp_dir = dir['tmp']

    video_path = os.path.join(cache_dir, video_id)
    tmp_path = os.path.join(tmp_dir, video_id)

    try:
        if not os.path.exists(video_path):
            if cache_remote_url(video_url, tmp_path, params):
                size = os.path.getsize(tmp_path)
                os.rename(tmp_path, video_path)
                os.chmod(video_path, mode)
                os.utime(video_path, None)
                info( { 'code' : VIDEO_CACHED, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Video was cached successfully.' } )
            else:
                return
        else:
            info({ 'code' : VIDEO_EXISTS, 'message' : 'Video already exists at ' + video_path + '.', 'website_id' : website_id, 'video_id' : video_id, 'client_ip' : client_ip })

        for vid in alternate_ids:
            try:
                new_video_path = os.path.join(cache_dir, vid)
                if new_video_path is not None:
                    if not os.path.exists(new_video_path):
                        os.link(video_path, new_video_path)
                    os.utime(new_video_path, None)
            except Exception, e:
                error( { 'code' : VIDEO_LINK_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Could not link video to alternate video id.', 'debug' : str(e) } )
                trace( { 'code' : VIDEO_LINK_ERR, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : traceback.format_exc() } )
                continue
        return
    except Exception, e:
        error( { 'code' : URL_CACHE_ERR, 'message' : 'Failed to cache video at ' + video_url + '.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
        trace( { 'code' : URL_CACHE_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
    return

def cache_generalized(params):
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    mode = 0644
    client_ip = params.get('client_ip', '-')
    video_id = params.get('video_id', '-')
    website_id = params.get('website_id', '-')
    urls = params.get('urls', [])
    dirs = params.get('dirs', [])

    if video_id == '-' or website_id == '-' or len(dirs) == 0 or len(urls) == 0:
        error( { 'code' : VIDEO_INFO2_ERR, 'message' : 'Enough video information was not available in cache thread.', 'website_id' : website_id, 'video_id' : video_id, 'client_ip' : client_ip } )
        return

    dir = dirs[0]

    cache_dir = dir['cache_dir']
    tmp_dir = dir['tmp']

    video_path = os.path.join(cache_dir, video_id)
    tmp_path = os.path.join(tmp_dir, video_id)

    for url in urls:
        original_url = url
        if website_id not in ['redtube', 'xtube', 'tube8']:
            url = refine_url(url, ['begin', 'start', 'noflv'])
        try:
            if not os.path.exists(video_path):
                if cache_remote_url(url, tmp_path, params):
                    size = os.path.getsize(tmp_path)
                    os.rename(tmp_path, video_path)
                    os.chmod(video_path, mode)
                    os.utime(video_path, None)
                    info( { 'code' : VIDEO_CACHED, 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip, 'message' : 'Video was cached successfully. ' + str(size) } )
                    return
            else:
                info({ 'code' : VIDEO_EXISTS, 'message' : 'Video already exists at ' + video_path + '.', 'website_id' : website_id, 'video_id' : video_id, 'client_ip' : client_ip })
            return
        except Exception, e:
            error( { 'code' : URL_CACHE_ERR, 'message' : 'Failed to cache video at ' + original_url + '.', 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
            trace( { 'code' : URL_CACHE_ERR, 'message' : traceback.format_exc(), 'video_id' : video_id, 'website_id' : website_id, 'client_ip' : client_ip } )
    return

cache_metacafe_video = cache_generalized
cache_dailymotion_video = cache_generalized
cache_google_video = cache_generalized
cache_redtube_video = cache_generalized
cache_xtube_video = cache_generalized
cache_vimeo_video = cache_generalized
cache_wrzuta_video = cache_generalized
cache_youporn_video = cache_generalized
cache_bing_video = cache_generalized
cache_tube8_video = cache_generalized
cache_bliptv_video = cache_generalized
cache_break_video = cache_generalized

def cache_thread_scheduler():
    info( { 'code' : CACHE_THREAD_SCHEDULER_START, 'message' : 'Starting cache thread scheduler.' } )
    connection()
    while True:
        try:
            if not o.offline_mode:
                num_tries = 0
                while num_tries < 5:
                    try:
                        video_pool.schedule()
                        break
                    except Exception, e:
                        connection()
                    num_tries += 1
                    time.sleep(min(2 ** num_tries, 10))
                else:
                    warn({ 'code' : CACHE_THREAD_SCHEDULE_FAIL, 'message' : 'Could not schedule a cache thread in ' + str(num_tries) + ' tries. Please check RPC server status.' })
        except Exception, e:
            warn({ 'code' : CACHE_THREAD_SCHEDULE_WARN, 'message' : 'Error in scheduling a cache thread. Continuing.', 'debug' : str(e)})
            trace({ 'code' : CACHE_THREAD_SCHEDULE_WARN, 'message' : traceback.format_exc() })
        time.sleep(5)

class VideoPoolDaemon(VideocacheDaemon):

    def __init__(self, o = None, **kwargs):
        self.o = o
        VideocacheDaemon.__init__(self, o.scheduler_pidfile, **kwargs)

    def run(self):
        global process_id
        try:
            self.o.set_loggers()
            process_id = os.getpid()
            server = VideoPoolRPCServer((self.o.rpc_host, int(self.o.rpc_port)), logRequests=0)
            server.register_function(server.shutdown)
            server.register_introspection_functions()
            server.register_instance(VideoPool())
            info( { 'code' : VIDEO_POOL_SERVER_START, 'message' : 'Starting VideoPool Server at port ' + str(self.o.rpc_port) + '.' } )

            server_thread = threading.Thread(target = server.serve_forever)
            cache_thread = threading.Thread(target = cache_thread_scheduler)
            server_thread.start()
            cache_thread.start()
            server_thread.join()
            cache_thread.join()
            #server.serve_forever()
        except Exception, e:
            error( { 'code' : VIDEO_POOL_SERVER_START_ERR, 'message' : 'Error while starting VideoPool server at port ' + str(self.o.rpc_port) + '.' } )
            trace( { 'code' : VIDEO_POOL_SERVER_START_ERR, 'message' : traceback.format_exc() } )
            sys.stdout.write(traceback.format_exc())

if __name__ == '__main__':
    # Parse command line options.
    parser = OptionParser()
    parser.add_option('-p', '--prefix', dest = 'vc_root', type='string', help = 'Specify an alternate root location for videocache', default = '/')
    parser.add_option('-c', '--config', dest = 'config_file', type='string', help = 'Use an alternate configuration file', default = '/etc/videocache.conf')
    parser.add_option('-s', '--signal', dest = 'sig', type='string', help = 'Send one of the following signals. start, stop, restart, reload, kill')
    options, args = parser.parse_args()

    if options.sig:
        try:
            o = VideocacheOptions(options.config_file, options.vc_root)
        except Exception, e:
            message = 'Could not load Videocache configuration file. \nDebugging output: \n' + traceback.format_exc()
            syslog_msg(message.replace('\n', ''))
            sys.stderr.write(message)
            sys.exit(1)

        uid = None
        try:
            uid = pwd.getpwnam( o.videocache_user ).pw_uid
        except Exception, e:
            try:
                uid = pwd.getpwnam( 'nobody' ).pw_uid
            except Exception, e:
                pass
        if uid == None:
            message = 'Could not determine User ID for videocache user ' + o.videocache_user + '. \nDebugging output: \n' + traceback.format_exc()
            syslog_msg(message.replace('\n', ''))
            sys.stderr.write(message)
            sys.exit(1)

        daemon = VideoPoolDaemon(o, uid = uid)

        video_pool = None
        exit = False
        process_id = '-'

        if options.sig == 'start':
            daemon.start()
        elif options.sig == 'stop':
            daemon.stop()
        elif options.sig == 'restart':
            daemon.restart()
        elif options.sig == 'reload':
            daemon.reload()
        elif options.sig == 'kill':
            daemon.kill()
        else:
            sys.stderr.write('Unknown signal received. See --help for more options.\n')
    else:
        sys.stderr.write('Nothing to do. Exiting. See --help for more options.\n')
        sys.exit(0)
