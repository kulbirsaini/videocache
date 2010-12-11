#!/usr/bin/env python

#
# (C) Copyright 2008-2010 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from config import readMainConfig, readStartupConfig
from optparse import OptionParser
from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer
import cgi
import cookielib
import logging
import logging.handlers
import os
import random
import re
import socket
import statvfs
import sys
import threading
import time
import urllib
import urllib2
import urlparse

# Parse command line options.
#parser = OptionParser()
#parser.add_option('--config')

mainconf =  readMainConfig(readStartupConfig('/etc/videocache.conf', '/'))

# Gloabl Options
enable_video_cache = int(mainconf.enable_video_cache)
base_dir_list = mainconf.base_dir.split('|')
base_dir = []
for dir in base_dir_list:
    try:
        dir_tup = [val.strip() for val in dir.split(':')]
        if len(dir_tup) == 1 or (len(dir_tup) == 2 and dir_tup[1] == ''):
            base_dir.append((dir_tup[0], 0))
        elif len(dir_tup) == 2:
            base_dir.append((dir_tup[0], int(dir_tup[1])))
    except Exception, e:
        # WTF?? Can't even set cache directories properly
        print >>sys.stderr, 'Videocache: Warning: Could not completely parse cache_dir from videocache.conf.'

temp_dir = mainconf.temp_dir
disk_avail_threshold = int(mainconf.disk_avail_threshold)
max_parallel_downloads = int(mainconf.max_parallel_downloads)
cache_host = mainconf.cache_host
hit_threshold = int(mainconf.hit_threshold)
rpc_host = mainconf.rpc_host
rpc_port = int(mainconf.rpc_port)
logfile = os.path.join(mainconf.logdir, 'videocache.log')
max_logfile_size = int(mainconf.max_logfile_size) * 1024 * 1024
max_logfile_backups = int(mainconf.max_logfile_backups)
proxy = mainconf.proxy
proxy_username = mainconf.proxy_username
proxy_password = mainconf.proxy_password

BASE_PLUGIN = 0
XMLRPC_SERVER = 1
DOWNLOAD_SCHEDULER = 2
redirect = '303'
format = '%s %s %s %s %s %s'
cache_url = 'http://' + str(cache_host) + '/' 
std_headers = {
    'User-Agent': 'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.8) Gecko/20100723 Firefox/3.6.8',
    'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-us,en;q=0.5',
}

# Cookie processor and default socket timeout
cj = cookielib.CookieJar()
urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)))
socket.setdefaulttimeout(120)

# Setup proxy
try:
    new_proxy = None
    if proxy and proxy_username and proxy_password:
        proxy_parts = urlparse.urlsplit(proxy)
        new_proxy = '%s://%s:%s@%s/' % (proxy_parts[0], proxy_username, proxy_password, proxy_parts[1])
    else:
        new_proxy = proxy
    if new_proxy:
        urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler( { 'http' : new_proxy } )))
    else:
        urllib2.install_opener(urllib2.build_opener(urllib2.ProxyHandler()))
except Exception, e:
    print >>sys.stderr, 'Videocache: Warning: Could not set proxy.'

def set_globals(type_low):
    enable_cache = int(eval('mainconf.enable_' + type_low + '_cache'))
    cache_dir = eval('mainconf.' + type_low + '_cache_dir')
    max_video_size = int(eval('mainconf.max_' + type_low + '_video_size'))
    min_video_size = int(eval('mainconf.min_' + type_low + '_video_size'))
    return (enable_cache, cache_dir, max_video_size, min_video_size)

# Website specific options
(enable_youtube_cache, youtube_cache_dir, max_youtube_video_size, min_youtube_video_size) = set_globals('youtube') 
(enable_metacafe_cache, metacafe_cache_dir, max_metacafe_video_size, min_metacafe_video_size) = set_globals('metacafe')
(enable_dailymotion_cache, dailymotion_cache_dir, max_dailymotion_video_size, min_dailymotion_video_size)=set_globals('dailymotion')
(enable_google_cache, google_cache_dir, max_google_video_size, min_google_video_size) = set_globals('google')
(enable_redtube_cache, redtube_cache_dir, max_redtube_video_size, min_redtube_video_size) = set_globals('redtube')
(enable_xtube_cache, xtube_cache_dir, max_xtube_video_size, min_xtube_video_size) = set_globals('xtube')
(enable_vimeo_cache, vimeo_cache_dir, max_vimeo_video_size, min_vimeo_video_size) = set_globals('vimeo')
(enable_wrzuta_cache, wrzuta_cache_dir, max_wrzuta_video_size, min_wrzuta_video_size) = set_globals('wrzuta')
(enable_youporn_cache, youporn_cache_dir, max_youporn_video_size, min_youporn_video_size) = set_globals('youporn')
(enable_soapbox_cache, soapbox_cache_dir, max_soapbox_video_size, min_soapbox_video_size) = set_globals('soapbox')
(enable_tube8_cache, tube8_cache_dir, max_tube8_video_size, min_tube8_video_size) = set_globals('tube8')
(enable_tvuol_cache, tvuol_cache_dir, max_tvuol_video_size, min_tvuol_video_size) = set_globals('tvuol')
(enable_bliptv_cache, bliptv_cache_dir, max_bliptv_video_size, min_bliptv_video_size) = set_globals('bliptv')
(enable_break_cache, break_cache_dir, max_break_video_size, min_break_video_size) = set_globals('break')

class Function_Thread(threading.Thread):
    def __init__(self, fid):
        threading.Thread.__init__(self)
        self.fid = fid
        return

    def run(self):
        if self.fid == XMLRPC_SERVER:
            start_xmlrpc_server()
        elif self.fid == DOWNLOAD_SCHEDULER:
            download_scheduler()
        elif self.fid == BASE_PLUGIN:
            squid_part()
        return

class VideoIDPool:
    """
    This class is for sharing the current packages being downloading
    across various instances of videocache via XMLRPC.
    """
    def __init__(self):
        self.scores = {}
        self.queue = {}
        self.active = []
        self.scheduler = None
        self.base_dir_size = {}
        for tup in base_dir:
            self.base_dir_size[tup[0]] = 0
        pass

    def new_video(self, video_id, values):
        """
        A new video is added to the queue and its score is set to 0.
        If video is already queued, score is incremented by 1.
        """
        if video_id in self.queue.keys():
            self.inc_score(video_id)
            [client, urls, video_id, type] = [i for i in self.queue[video_id]]
            [client, new_urls, video_id, type] = [i for i in values]
            self.queue[video_id] = [client, list(set(urls + new_urls)), video_id, type]
        else:
            self.queue[video_id] = values
            self.scores[video_id] = 1
        return True

    def get_score(self, video_id):
        """Get the score of video represented by video_id."""
        if video_id in self.scores.keys():
            return self.scores[video_id]
        else:
            return 0

    def set_score(self, video_id, score = 1):
        """Set the priority score of a video_id."""
        self.scores[video_id] = score
        return True

    def inc_score(self, video_id, incr = 1):
        """Increase the priority score of video represented by video_id."""
        if video_id in self.scores.keys():
            self.scores[video_id] += incr
        return True

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
        if video_id in self.queue.keys():
            self.queue.pop(video_id)
        if video_id in self.scores.keys():
            self.scores.pop(video_id)
        return True

    def remove_url_from_queue(self, video_id, url):
        """Dequeue a url for a video_id from the download queue."""
        if video_id in self.queue.keys():
            if url in self.queue[video_id]:
                self.queue[video_id][1].remove(url)
        return True

    def remove(self, video_id):
        """Remove video_id from queue as well as active connection list."""
        return self.remove_from_queue(video_id) and self.remove_conn(video_id)

    def remove_url(self, video_id, url):
        """Remove url from url list for a video_id."""
        if len(self.queue[video_id][1]) == 1:
            return self.remove_from_queue(video_id) and self.remove_conn(video_id)
        else:
            return self.remove_url_from_queue(video_id, url) and self.remove_conn(video_id)

    def flush(self):
        """Flush the queue and reinitialize everything."""
        self.queue = {}
        self.scores = {}
        self.active = []
        return True

    def schedule(self):
        """Returns the parameters for a video to be downloaded from remote."""
        pid = os.getpid()
        try:
            if self.get_conn_number() < max_parallel_downloads:
                video_id = self.get_popular()
                if video_id != False and self.is_active(video_id) == False and self.get_score(video_id) >= hit_threshold:
                    params = self.get_details(video_id)
                    if params != False:
                        self.set_score(video_id, 0)
                        self.add_conn(video_id)
                        return params
                elif self.is_active(video_id) == True:
                    self.set_score(video_id, 0)
                    return False
                else:
                    return False
            else:
                return False
        except Exception, e:
            log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', str(e)))
        return True

    def set_scheduler(self, pid):
        if self.scheduler is None:
            self.scheduler = pid
        else:
            return False
        return True

    def set_cache_dir_size(self, cache_dir, size):
        """Sets the size of a cache directory."""
        if cache_dir in self.base_dir_size.keys():
            self.base_dir_size[cache_dir] = size
            return True
        return False

    def get_cache_dir_size(self, cache_dir):
        """Returns the size of a cache directory."""
        if cache_dir in self.base_dir_size.keys():
            return self.base_dir_size[cache_dir]
        return -1

    # Functions related download scheduling.
    # Have to mess up things in single class because python
    # XMLRPCServer doesn't allow to register multiple instances
    # via register_instance
    def add_conn(self, video_id):
        """Add video_id to active connections list."""
        if video_id not in self.active:
            self.active.append(video_id)
        return True

    def get_conn_number(self):
        """Return the number of currently active connections."""
        return len(self.active)

    def is_active(self, video_id):
        """Returns whether a connection is active or not."""
        if video_id in self.active:
            return True
        return False

    def remove_conn(self, video_id):
        """Remove video_id from active connections list."""
        if video_id in self.active:
            self.active.remove(video_id)
        return True

class MyXMLRPCServer(SimpleXMLRPCServer):

    request_queue_size = 10
    allow_reuse_address = True

    def __init__(self, *args, **kwargs):
        self.finished = False
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    def shutdown(self):
        self.finished = True
        return 1

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)

    def serve_forever(self):
        while not self.finished:
            self.handle_request()

def set_logging():
    try:
        logger = logging.Logger('VideocacheLog', )
        logger.setLevel(logging.DEBUG)
        handler = logging.handlers.RotatingFileHandler(logfile, mode = 'a', maxBytes = max_logfile_size, backupCount = max_logfile_backups)
        handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
        logger.addHandler(handler)
        return logger
    except Exception, e:
        # Logged to squid's cache.log
        print >>sys.stderr, 'Videocache: Error: Could not initialize logging.'
        print >>sys.stderr, 'Videocache: Error: Please check /var/log/videocache/ or cache_dir for ownership and permission problems.'
        return None

def get_cache_size(cache_dir):
    """
    Returned size is in Mega Bytes.
    """
    pid = os.getpid()
    size = 0
    try:
        for (path, dirs, files) in os.walk(cache_dir):
            for file in files:
                filename = os.path.join(path, file)
                size += os.path.getsize(filename)
                time.sleep(0.000001)
    except Exception, e:
        log(format%(pid, '-', '-', 'CACHE_SIZE_ERR', cache_dir, str(e)))
        return -1
    return size / (1024*1024)

def remove(video_id):
    """Remove video_id from queue."""
    try:
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        video_id_pool.remove(video_id)
    except Exception, e:
        log(format%(os.getpid(), '-', '-', 'DEQUEUE_ERR', '-', str(e)))
    return

def remove_url(video_id, url):
    """Remove url from url list for a video_id"""
    try:
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        video_id_pool.remove_url(video_id, url)
    except Exception, e:
        log(format%(os.getpid(), '-', '-', 'DEQUEUE_URL_ERR', '-', str(e)))
    return

def fork(f):
    """This function is highly inspired from concurrency in python
    tutorial at http://blog.buffis.com/?p=63 .
    Generator for creating a forked process from a function"""
    # Perform double fork
    r = ''
    if os.fork(): # Parent
        # Wait for the child so that it doesn't get defunct
        os.wait()
        # Return a function
        return  lambda *x, **kw: r 

    # Otherwise, we are the child 
    # Perform second fork
    os.setsid()
    os.umask(077)
    os.chdir('/')
    if os.fork():
        os._exit(0) 

    def wrapper(*args, **kwargs):
        """Wrapper function to be returned from generator.
        Executes the function bound to the generator and then
        exits the process"""
        f(*args, **kwargs)
        os._exit(0)

    return wrapper

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

def refine_url(url, arg_drop_list = []):
    """Returns a refined url with all the arguments mentioned in arg_drop_list dropped."""
    params = urlparse.urlsplit(url)[3]
    arglist = params.split('&')
    query = ''
    for arg in arglist:
        try:
            pair = arg.split('=')
            if pair[0] in arg_drop_list:
                continue
            else:
                query += arg + '&'
        except Exception, e:
            continue
    return (urllib.splitquery(url)[0] + '?' + query.rstrip('&')).rstrip('?')

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
            result = download(video_url, download_path)
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
                result = download(url, download_path)
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

def download(remote_url, target_file):
    request = urllib2.Request(remote_url, None, std_headers)
    connection = urllib2.urlopen(request)
    try:
        file = None
        while True:
            block = connection.read(8192)
            if len(block) == 0:
                break
            if not file:
                file = open(target_file, 'wb')
            file.write(block)
        if file:
            file.close()
    except urllib2.HTTPError, e:
        try:
            return [None, 'DOWNLOAD_HTTP_ERR', 'HTTP ERROR : ' + str(e.code) + ' : An error occured while retrieving the video.  '  + remote_url ]
        except:
            return [None, 'DOWNLOAD_HTTP_ERR', 'HTTP ERROR : ' + str(e) + ' : An error occured while retrieving the video.  '  + remote_url ]
    except Exception, e:
        return [None, 'DOWNLOAD_ERR', str(e)]
    return [True, None, None]

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

def queue(video_id, values):
    """Queue a video for download."""
    try:
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        video_id_pool.new_video(video_id, values)
    except Exception, e:
        log(format%(os.getpid(), '-', '-', 'QUEUE_ERR', '-', str(e)))
    return

def cache_video(client, url, type, video_id, cache_check_only = False):
    """This function check whether a video is in cache or not. If not, it fetches
    it from the remote source and cache it and also streams it to the client."""
    global cache_url
    pid = os.getpid()

    params = urlparse.urlsplit(url)[3]
    type_low = type.lower()
    for index in range(len(base_dir)):
        # Pick up cache directories one by one.
        try:
            path = os.path.join(base_dir[index][0], eval(type_low + '_cache_dir'), video_id)
            if len(base_dir) == 1:
                index = ''
            cached_url = os.path.join(cache_url, 'videocache', str(index) ,type_low)
        except Exception, e:
            log(format%(pid, client, video_id, 'PARAM_ERR', type, '(cache_video_fun) : ' + str(e)))
            continue

        # If video is found, heads up!!! Return it.
        if os.path.isfile(path):
            log(format%(pid, client, video_id, 'CACHE_HIT', type, 'Video was served from cache.'))
            os.utime(path, None)
            url = os.path.join(cached_url, video_id) + '?' + params
            if type == 'YOUTUBE' and not cache_check_only:
                forked = fork(queue)
                forked(video_id, [client, [url], video_id, type])
            return redirect + ':' + refine_url(url, ['noflv'])
  
    if not cache_check_only:
        log(format%(pid, client, video_id, 'CACHE_MISS', type, 'Requested video was not found in cache.'))
        # Queue video using daemon forking as it'll save time in returning the url.
        forked = fork(queue)
        forked(video_id, [client, [url], video_id, type])
    return url

def submit_video(pid, client, type, url, video_id, cache_check_only = False):
    if not cache_check_only:
        log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
    new_url = cache_video(client, url[0], type, video_id, cache_check_only)
    if not cache_check_only:
        log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
    return new_url

def squid_part():
    """This function will tap requests from squid. If the request is for a 
    video, they will be forwarded to function cache_video() for further processing.
    Finally this function will flush a cache_url if package found in cache or a
    blank line in case on a miss to stdout. This is the only function where we deal
    with squid, rest of the program/project doesn't interact with squid at all."""
    pid = os.getpid()
    while True:
        try:
            # Read url from stdin (this is provided by squid)
            url = sys.stdin.readline().strip().split(' ')
            new_url = url[0];
            # Retrieve the basename from the request url
            fragments = urlparse.urlsplit(url[0])
            [host, path, params] = [fragments[1], fragments[2], fragments[3]]
            client = url[1].split('/')[0]
            log(format%(pid, client, '-', 'REQUEST', '-', url[0]))
        except IOError, e:
            if e.errno == 32:
                os.kill(os.getpid(), 1)
        except IndexError, e:
            log(format%(pid, '-', '-', 'RELOAD', '-', 'videocache plugin was reloaded.'))
            os.kill(os.getpid(), 1)

        # Check if videocache plugin is on.
        if enable_video_cache:
            # Youtube.com caching is handled here.
            if enable_youtube_cache:
                if host.find('.youtube.com') > -1 and path.find('get_video') > -1 and path.find('get_video_info') < 0:
                    type = 'YOUTUBE'
                    arglist = params.split('&')
                    dict = {}
                    for arg in arglist:
                        try:
                            dict[arg.split('=')[0]] = arg.split('=')[1]
                        except Exception, e:
                            continue
                    if dict.has_key('video_id'):
                        video_id = dict['video_id']
                        new_url = submit_video(pid, client, type, url, video_id)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'video_id not found in ' + new_url))

            # Youtube videos served via cache.googlevideo.com are handled here.
            # This code has been merged with Google.com videos
            
            # Metacafe.com caching is handled here.
            if enable_metacafe_cache:
                if (host.find('.mccont.com') > -1 or host.find('akvideos.metacafe.com') > -1 )and path.find('ItemFiles') > -1:
                    type = 'METACAFE'
                    try:
                        video_id = urllib2.unquote(path).strip('/').split(' ')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Dailymotion.com caching is handled here.
            if enable_dailymotion_cache:
                if (re.compile('proxy[a-z0-9\-][a-z0-9][a-z0-9][a-z0-9]?\.dailymotion\.com').search(host) or host.find('vid.akm.dailymotion.com') > -1 or host.find('.cdn.dailymotion.com') > -1)  and (path.find('flv') > -1 or path.find('.on2') > -1 or path.find('mp4') > -1 or path.find('aac') > -1 or path.find('h264') > -1 or path.find('h263') > -1):
                    type = 'DAILYMOTION'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        if (video_id.find('flv') > -1 or video_id.find('.on2') > -1 or video_id.find('mp4') > -1 or video_id.find('aac') > - 1 or video_id.find('h264') > -1 or video_id.find('h263') > -1):
                            new_url = submit_video(pid, client, type, url, video_id)
            
            # Google.com caching is handled here. get_video
            if enable_google_cache:
                if (host.find('.youtube.com') > -1 or re.compile('\.youtube\.[a-z][a-z]').search(host) or host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.google\.[a-z][a-z]').search(host) or re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host)) and (path.find('get_video') > -1) and path.find('get_video_info') < 0:
                    type = 'YOUTUBE'
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
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'docid not found in ' + new_url))
            
            # Google.com caching is handled here. videoplayback
            if enable_google_cache:
                if (host.find('.youtube.com') > -1 or re.compile('\.youtube\.[a-z][a-z]').search(host) or host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.google\.[a-z][a-z]').search(host) or re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host)) and (path.find('videoplayback') > -1 or path.find('videoplay') > -1) and path.find('get_video_info') < 0:
                    type = 'YOUTUBE'
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
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id, True)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'docid not found in ' + new_url))
            
            # Redtube.com caching is handled here.
            if enable_redtube_cache:
                if host.find('.redtube.com') > -1 and path.find('.flv') > -1:
                    type = 'REDTUBE'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Xtube.com caching is handled here.
            if enable_xtube_cache:
                if re.compile('[0-9a-z][0-9a-z][0-9a-z]?[0-9a-z]?[0-9a-z]?\.xtube\.com').search(host) and path.find('videos/') > -1 and path.find('.flv') > -1 and path.find('Thumb') < 0 and path.find('av_preview') < 0:
                    type = 'XTUBE'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Vimeo.com caching is handled here.
            if enable_vimeo_cache:
                if host.find('.vimeo.com') > -1 and (path.find('.flv') > -1 or path.find('.mp4') > -1):
                    type = 'VIMEO'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Wrzuta.pl audio file caching is handled here.
            if enable_wrzuta_cache:
                if host.find('va.wrzuta.pl') > -1 and re.compile('wa[0-9][0-9][0-9][0-9]?').search(path) and params.find('type=a') > -1 and params.find('key=') > -1:
                    type = 'WRZUTA'
                    arglist = params.split('&')
                    dict = {}
                    for arg in arglist:
                        try:
                            dict[arg.split('=')[0]] = arg.split('=')[1]
                        except Exception, e:
                            continue
                    if dict.has_key('key'):
                        video_id = dict['key']
                        new_url = submit_video(pid, client, type, url, video_id)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'key not found in ' + new_url))
            
            # Youporn.com audio file caching is handled here.
            if enable_youporn_cache:
                if host.find('.youporn.com') > -1 and path.find('.flv') > -1:
                    type = 'YOUPORN'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Soapbox.msn.com audio file caching is handled here.
            if enable_soapbox_cache:
                if host.find('.msn.com.edgesuite.net') > -1 and path.find('.flv') > -1:
                    type = 'SOAPBOX'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Tube8.com Video file caching is handled here.
            if enable_tube8_cache:
                if re.compile('\.tube8\.com').search(host) and (path.find('.flv') > -1 or path.find('.3gp') > -1):
                    type = 'TUBE8'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Tvuol.uol.com.br Video file caching is handled here.
            if enable_tvuol_cache:
                if host.find('mais.uol.com.br') > -1 and path.find('.flv') > -1:
                    type = 'TVUOL'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Blip.tv Video file caching is handled here.
            if enable_bliptv_cache:
                if re.compile('\.blip\.tv').search(host) and (path.find('.flv') > -1 or path.find('.wmv') > -1 or path.find('.mp4') > -1 or path.find('.rm') > -1 or path.find('.ram') > -1 or path.find('.mov') > -1 or path.find('.avi') > -1 or path.find('.m4v') > -1 or path.find('.mp3') > -1 or path.find('.m4v') > -1) :
                    type = 'BLIPTV'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Break.com Video file caching is handled here.
            if enable_break_cache:
                if host.find('.break.com') > -1 and (path.find('.flv') > -1 or path.find('.mp4') > -1):
                    type = 'BREAK'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
        # Flush the new url to stdout for squid to process
        try:
            sys.stdout.write(new_url + '\n')
            sys.stdout.flush()
        except IOError, e:
            if e.errno == 32:
                os.kill(os.getpid(), 1)

def start_xmlrpc_server():
    """Starts the XMLRPC server in a threaded process."""
    pid = os.getpid()
    try:
        server = MyXMLRPCServer((rpc_host, rpc_port), logRequests=0)
        #server = MyXMLRPCServer((rpc_host, rpc_port), logRequests=1)
        server.register_function(server.shutdown)
        server.register_introspection_functions()
        server.register_instance(VideoIDPool())
        log(format%(pid, '-', '-', 'XMLRPCSERVER', '-', 'Starting XMLRPCServer on port ' + str(rpc_port) + '.'))
        server.serve_forever()
        log(format%(pid, '-', '-', 'XMLRPCSERVER_STOP', '-', 'Stopping XMLRPCServer.'))
    except Exception, e:
        #log(format%(pid, '-', '-', 'START_XMLRPC_SERVER_ERR', '-', 'Cannot start XMLRPC Server - Exiting'))
        os.kill(pid, 1)

def update_cache_size():
    """Calculates the size of cache directories and informs the XMLRPC server."""
    try:
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        for (base_path, base_path_size) in base_dir:
            video_id_pool.set_cache_dir_size(base_path, get_cache_size(base_path))
        log(format%(os.getpid(), '-', '-', 'UPDATE_SIZE', '-', 'Size of all caching directories updated successfully.'))
    except Exception, e:
        log(format%(os.getpid(), '-', '-', 'UPDATE_SIZE_ERR', '-', str(e)))
    return

def download_scheduler():
    """Schedule videos from download queue for downloading."""
    pid = os.getpid()
    log(format%(pid, '-', '-', 'SCHEDULER', '-', 'Download Scheduler starting.'))
    time.sleep(random.random()*100%2)
    try:
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        if not video_id_pool.set_scheduler(pid):
            return
    except Exception, e:
        log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', '(while initializing scheduler) : ' + str(e)))

    wait_time = 20
    update_cache_size_time = 0
    video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
    while True:
        try:
            params = video_id_pool.schedule()
            if params == False:
                wait_time = 5
            elif params == True:
                wait_time = 0.2
            else:
                try:
                    forked = fork(download_from_source)
                    forked(params)
                    log(format%(pid, params[0], params[2], 'SCHEDULED', params[3], 'Video scheduled for download.'))
                    wait_time = 0.2
                    update_cache_size_time -= 1
                except Exception, e:
                    remove(params[2])
                    log(format%(pid, '-', '-', 'SCHEDULED_ERR', '-', str(e)))
                    wait_time = 0.5
        except Exception, e:
            log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', str(e)))
        time.sleep(wait_time)
    log(format%(pid, '-', '-', 'SCHEDULEDER_STOP', '-', 'Download Scheduler stopping.'))
    return

if __name__ == '__main__':
    global log
    logger = set_logging()
    if not logger:
        sys.exit(1)
    log = logger.info

    if log is not None:
        # If XMLRPCServer is running already, don't start it again
        try:
            time.sleep(random.random()*100%7)
            video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
            # Flush previous values on reload
            video_id_pool.flush()
            # For testing with squid, use this function
            squid_part()
        except Exception, e:
            # Start XMLRPC Server, Download Scheduler and Base Plugin in threads.
            thread_xmlrpc = Function_Thread(XMLRPC_SERVER)
            thread_download_scheduler = Function_Thread(DOWNLOAD_SCHEDULER)
            thread_base_plugin = Function_Thread(BASE_PLUGIN)
            thread_xmlrpc.start()
            thread_download_scheduler.start()
            thread_base_plugin.start()
            thread_xmlrpc.join()
            thread_download_scheduler.join()
            thread_base_plugin.join()
    else:
        print >>sys.stderr, 'Videocache: Error: Logging facility is not available.'

