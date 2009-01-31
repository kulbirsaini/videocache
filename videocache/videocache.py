#!/usr/bin/env python

# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
# (C) Copyright 2008 Kulbir Saini <kulbirsaini@students.iiit.ac.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <kulbirsaini@students.iiit.ac.in>"""
__docformat__ = 'plaintext'

from config import readMainConfig, readStartupConfig
from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer
import logging
import logging.handlers
import os
import random
import re
import socket
import stat
import sys
import threading
import time
import urlgrabber
import urllib2
import urlparse

mainconf =  readMainConfig(readStartupConfig('/etc/videocache.conf', '/'))

# Gloabl Options
enable_video_cache = int(mainconf.enable_video_cache)
base_dir = [dir.strip() for dir in mainconf.base_dir.strip().split('|')]
temp_dir = mainconf.temp_dir
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

def set_globals(type_low):
    enable_cache = int(eval('mainconf.enable_' + type_low + '_cache'))
    cache_dir = eval('mainconf.' + type_low + '_cache_dir')
    cache_size = int(eval('mainconf.' + type_low + '_cache_size'))
    max_video_size = int(eval('mainconf.max_' + type_low + '_video_size'))
    min_video_size = int(eval('mainconf.min_' + type_low + '_video_size'))
    return (enable_cache, cache_dir, cache_size, max_video_size, min_video_size)

# Youtube specific options
(enable_youtube_cache, youtube_cache_dir, youtube_cache_size, max_youtube_video_size, min_youtube_video_size) = set_globals('youtube') 
(enable_metacafe_cache, metacafe_cache_dir, metacafe_cache_size, max_metacafe_video_size, min_metacafe_video_size) = set_globals('metacafe')
(enable_dailymotion_cache, dailymotion_cache_dir, dailymotion_cache_size, max_dailymotion_video_size, min_dailymotion_video_size)=set_globals('dailymotion')
(enable_google_cache, google_cache_dir, google_cache_size, max_google_video_size, min_google_video_size) = set_globals('google')
(enable_redtube_cache, redtube_cache_dir, redtube_cache_size, max_redtube_video_size, min_redtube_video_size) = set_globals('redtube')
(enable_xtube_cache, xtube_cache_dir, xtube_cache_size, max_xtube_video_size, min_xtube_video_size) = set_globals('xtube')
(enable_vimeo_cache, vimeo_cache_dir, vimeo_cache_size, max_vimeo_video_size, min_vimeo_video_size) = set_globals('vimeo')
(enable_wrzuta_cache, wrzuta_cache_dir, wrzuta_cache_size, max_wrzuta_video_size, min_wrzuta_video_size) = set_globals('wrzuta')
(enable_youporn_cache, youporn_cache_dir, youporn_cache_size, max_youporn_video_size, min_youporn_video_size) = set_globals('youporn')
(enable_soapbox_cache, soapbox_cache_dir, soapbox_cache_size, max_soapbox_video_size, min_soapbox_video_size) = set_globals('soapbox')
(enable_tube8_cache, tube8_cache_dir, tube8_cache_size, max_tube8_video_size, min_tube8_video_size) = set_globals('tube8')
(enable_tvuol_cache, tvuol_cache_dir, tvuol_cache_size, max_tvuol_video_size, min_tvuol_video_size) = set_globals('tvuol')
(enable_bliptv_cache, bliptv_cache_dir, bliptv_cache_size, max_bliptv_video_size, min_bliptv_video_size) = set_globals('bliptv')
(enable_break_cache, break_cache_dir, break_cache_size, max_break_video_size, min_break_video_size) = set_globals('break')

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
        pass

    def schedule(self):
        pid = os.getpid()
        try:
            if self.get_conn_number() < max_parallel_downloads:
                video_id = self.get_popular()
                if video_id != "NULL" and self.is_active(video_id) == False and self.get_score(video_id) >= hit_threshold:
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
        except:
            log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', 'Error in schedule function.'))
        return True

    def new_video(self, video_id):
        if video_id in self.queue.keys():
            self.inc_score(video_id)
            return False
        else:
            self.add(video_id)
            return True

    def set_scheduler(self, pid):
        if self.scheduler is None:
            self.scheduler = pid
        else:
            return False
        return True

    # Functions related to video_id queue-ing.
    def add(self, video_id, score = 1):
        """Queue a video_id for download. Score defaults to one."""
        if video_id not in self.queue.keys():
            self.queue[video_id] = []
        self.scores[video_id] = score
        return True

    def set(self, video_id, values):
        """Set the details of video_id to values."""
        self.queue[video_id] = values
        return True

    def set_score(self, video_id, score = 1):
        """Set the priority score of a video_id."""
        self.scores[video_id] = score
        return True

    def inc_score(self, video_id, incr = 1):
        """Increase the priority score of video represented by video_id."""
        if video_id in self.scores.keys():
            self.scores[video_id] += incr
        return True

    def get_score(self, video_id):
        """Get the score of video represented by video_id."""
        if video_id in self.scores.keys():
            return self.scores[video_id]
        else:
            return 0

    def get(self):
        """Return all the video ids currently in queue."""
        return self.queue.keys()

    def get_details(self, video_id):
        """Return the details of a particular video represented by video_id."""
        if video_id in self.queue.keys():
            return self.queue[video_id]
        return False

    def get_popular(self):
        """Return the video_id of the most frequently access video."""
        vk = [(v,k) for k,v in self.scores.items()]
        if len(vk) != 0:
            video_id = sorted(vk, reverse=True)[0][1]
            return video_id
        return "NULL"

    def remove(self, video_id):
        """Dequeue a video_id from the download queue."""
        if video_id in self.queue.keys():
            self.queue.pop(video_id)
        if video_id in self.scores.keys():
            self.scores.pop(video_id)
        return True

    def flush(self):
        """Flush the queue and reinitialize everything."""
        self.queue = {}
        self.scores = {}
        self.active = []
        return True

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

    def remove_all(self, video_id):
        """Remove video_id from queue as well as active connection list."""
        self.remove(video_id)
        self.remove_conn(video_id)
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

def set_proxy():
    try:
        if proxy_username and proxy_password:
            proxy_parts = urlparse.urlsplit(proxy)
            new_proxy = '%s://%s:%s@%s/' % (proxy_parts[0], proxy_username, proxy_password, proxy_parts[1])
        else:
            new_proxy = proxy
        return urlgrabber.grabber.URLGrabber(proxies = {'http': new_proxy})
    except:
        log(format%(os.getpid(), '-', '-', 'PROXY_ERR', '-', 'Error in setting proxy server.'))
        return None

def set_logging():
    try:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(message)s',
                            filename=logfile,
                            filemode='a')
        return logging.info
    except:
        # No idea where to log. May be logged to syslog.
        return None

def dir_size(dir):
    """
    This is not a standard function to calculate the size of a directory.
    This function will only give the sum of sizes of all the files in 'dir'.
    """
    # Initialize with 4096bytes as the size of an empty dir is 4096bytes.
    size = 4096
    try:
        for file in os.listdir(dir):
            size += int(os.stat(os.path.join(dir, file))[6])
    except:
        return -1
    return size / (1024*1024)

def remove(video_id):
    """Remove video_id from queue."""
    try:
        video_id_pool.remove_all(video_id)
    except:
        log(format%(os.getpid(), '-', '-', 'DEQUEUE_ERR', '-', 'Error querying XMLRPC Server.'))
    return

def queue(video_id, values):
    """Queue video_id for scheduling later by download_scheduler."""
    try:
        video_id_pool.set(video_id, values)
    except:
        log(format%(os.getpid(), '-', '-', 'QUEUE_ERR', '-', 'Error querying XMLRPC Server.'))
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

def download_from_source(args):
    """This function downloads the file from remote source and caches it."""
    pid = os.getpid()
    try:
        [client, url, path, mode, video_id, type, max_size, min_size, cache_size, cache_dir, tmp_cache] = [i for i in args]
    except:
        log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', 'Scheduler didn\'t provide enough information.'))
        remove(video_id)
        return

    if cache_size != 0 and dir_size(cache_dir) >= cache_size:
        log(format%(pid, client, video_id, 'CACHE_FULL', type, 'Cache directory \'' + cache_dir + '\' has exceeded the maximum size allowed.'))
        remove(video_id)
        return

    grabber = set_proxy()
    if grabber is None:
        remove(video_id)
        return

    if max_size or min_size:
        try:
            log(format%(pid, client, video_id, 'GET_SIZE', type, 'Trying to get the size of video.'))
            remote_file = grabber.urlopen(url)
            remote_size = int(remote_file.info().getheader('content-length')) / 1024
            remote_file.close()
            log(format%(pid, client, video_id, 'GOT_SIZE', type, str(remote_size) + ' Successfully retrieved the size of video.'))
        except:
            remove(video_id)
            log(format%(pid, client, video_id, 'SIZE_ERR', type, 'Could not retrieve size of the video.'))
            return

        if max_size and remote_size > max_size:
            remove(video_id)
            log(format%(pid, client, video_id, 'MAX_SIZE', type, 'Video size ' + str(remote_size) + ' is larger than maximum allowed.'))
            return
        if min_size and remote_size < min_size:
            remove(video_id)
            log(format%(pid, client, video_id, 'MIN_SIZE', type, 'Video size ' + str(remote_size) + ' is smaller than minimum allowed.'))
            return

    try:
        download_path = os.path.join(tmp_cache, os.path.basename(path))
        open(download_path, 'a').close()
        file = grabber.urlgrab(url, download_path)
        size = os.stat(file)[6]
        os.rename(file, path)
        os.chmod(path, mode)
        remove(video_id)
        log(format%(pid, client, video_id, 'DOWNLOAD', type, str(size) + ' Video was downloaded and cached.'))
    except:
        remove(video_id)
        log(format%(pid, client, video_id, 'DOWNLOAD_ERR', type, 'An error occured while retrieving the video.'))
    return

def video_params(base_path, video_id, type, url, index = ''):
    type_low = type.lower()
    params = urlparse.urlsplit(url)[3]
    path = os.path.join(base_path, eval(type_low + '_cache_dir'), video_id)
    cached_url = os.path.join(cache_url, 'videocache', str(index) ,type_low)
    max_size = eval('max_' + type_low + '_video_size')
    min_size = eval('min_' + type_low + '_video_size')
    cache_size = eval(type_low + '_cache_size')
    cache_dir = os.path.join(base_path, eval(type_low + '_cache_dir'))
    tmp_cache = os.path.join(base_path, temp_dir)
    return (params, path, cached_url, max_size, min_size, cache_size, cache_dir, tmp_cache)

def cache_video(client, url, type, video_id):
    """This function check whether a video is in cache or not. If not, it fetches
    it from the remote source and cache it and also streams it to the client."""
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    global cache_url
    pid = os.getpid()
    mode = 0644
    index = None
    for base_path in base_dir:
        try:
            (params, path, cached_url, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params(base_path, video_id, type, url, base_dir.index(base_path))
            log(format%(path, cached_url, cache_dir, tmp_cache, type, 'An error occured while queueing the video.'))
        except:
            log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
            continue

        if os.path.isfile(path):
            remove(video_id)
            log(format%(pid, client, video_id, 'CACHE_HIT', type, 'Video was served from cache.'))
            return redirect + ':' + os.path.join(cached_url, video_id) + '?' + params
        else:
            if cache_size != 0 and dir_size(cache_dir) >= cache_size:
                log(format%(pid, client, video_id, 'CACHE_FULL', type, 'Cache directory \'' + cache_dir + '\' has exceeded the maximum size allowed.'))
                continue
            else:
                index = base_dir.index(base_path)
                continue
    if index is not None:
        (params, path, cached_url, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params(base_dir[index], video_id, type, url, index)
        log(format%(pid, client, video_id, 'CACHE_MISS', type, 'Requested video was not found in cache.'))
        queue(video_id, [client, url, path, mode, video_id, type, max_size, min_size, cache_size, cache_dir, tmp_cache])
        return url

    remove(video_id)
    return url

def submit_video(pid, client, type, url, video_id):
    try:
        result = video_id_pool.new_video(video_id)
        if result == True:
            log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
            new_url = cache_video(client, url[0], type, video_id)
            log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
            return new_url
    except:
        log(format%(pid, client, video_id, 'XMLRPC_ERR', type, 'Error querying RPC server'))
    return url[0]

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
            os.system('rm -f ' + temp_dir + '/* ')
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
                        except:
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
                if host.find('v.mccont.com') > -1 and path.find('ItemFiles') > -1:
                    type = 'METACAFE'
                    try:
                        video_id = urllib2.unquote(path).strip('/').split(' ')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Dailymotion.com caching is handled here.
            if enable_dailymotion_cache:
                if (re.compile('proxy[a-z0-9\-][a-z0-9][a-z0-9][a-z0-9]?\.dailymotion\.com').search(host) or host.find('vid.akm.dailymotion.com') > -1 or host.find('.cdn.dailymotion.com') > -1)  and (path.find('.flv') > -1 or path.find('.on2') > -1):
                    type = 'DAILYMOTION'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Google.com caching is handled here.
            if enable_google_cache:
                if (host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.google\.[a-z][a-z]').search(host)) and (path.find('videoplayback') > -1 or path.find('get_video') > -1) and path.find('get_video_info') < 0:
                    type = 'YOUTUBE'
                    arglist = params.split('&')
                    dict = {}
                    for arg in arglist:
                        try:
                            dict[arg.split('=')[0]] = arg.split('=')[1]
                        except:
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
            
            # Redtube.com caching is handled here.
            if enable_redtube_cache:
                if host.find('dl.redtube.com') > -1 and path.find('.flv') > -1:
                    type = 'REDTUBE'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Xtube.com caching is handled here.
            if enable_xtube_cache:
                if re.compile('[0-9a-z][0-9a-z][0-9a-z]?[0-9a-z]?[0-9a-z]?\.xtube\.com').search(host) and path.find('videos/') > -1 and path.find('.flv') > -1 and path.find('Thumb') < 0 and path.find('av_preview') < 0:
                    type = 'XTUBE'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Vimeo.com caching is handled here.
            if enable_vimeo_cache:
                if host.find('bitcast.vimeo.com') > -1 and path.find('vimeo/videos/') > -1 and path.find('.flv') > -1:
                    type = 'VIMEO'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
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
                        except:
                            continue
                    if dict.has_key('key'):
                        video_id = dict['key']
                        new_url = submit_video(pid, client, type, url, video_id)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'key not found in ' + new_url))
            
            # Youporn.com audio file caching is handled here.
            if enable_youporn_cache:
                if host.find('.files.youporn.com') > -1 and path.find('/flv/') > -1 and path.find('.flv') > -1:
                    type = 'YOUPORN'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Soapbox.msn.com audio file caching is handled here.
            if enable_soapbox_cache:
                if host.find('.msn.com.edgesuite.net') > -1 and path.find('.flv') > -1:
                    type = 'SOAPBOX'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Tube8.com Video file caching is handled here.
            if enable_tube8_cache:
                if re.compile('media[a-z0-9]?[a-z0-9]?[a-z0-9]?\.tube8\.com').search(host) and (path.find('.flv') > -1 or path.find('.3gp') > -1):
                    type = 'TUBE8'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Tvuol.uol.com.br Video file caching is handled here.
            if enable_tvuol_cache:
                if host.find('mais.uol.com.br') > -1 and path.find('.flv') > -1:
                    type = 'TVUOL'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Blip.tv Video file caching is handled here.
            if enable_bliptv_cache:
                if re.compile('\.video[a-z0-9]?[a-z0-9]?\.blip\.tv').search(host) and (path.find('.flv') > -1 or path.find('.wmv') > -1 or path.find('.mp4') > -1 or path.find('.rm') > -1 or path.find('.ram') > -1 or path.find('.mov') > -1 or path.find('.avi') > -1 or path.find('.m4v') > -1 or path.find('.mp3') > -1) :
                    type = 'BLIPTV'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
            
            # Break.com Video file caching is handled here.
            if enable_break_cache:
                if host.find('video.break.com') > -1 and (path.find('.flv') > -1 or path.find('.mp4')):
                    type = 'BREAK'
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Error in parsing the url ' + new_url))
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

def log_rotate():
    # Rotate logfiles if the size is more than the max_logfile_size.
    if os.stat(logfile)[6] > max_logfile_size:
        roll = logging.handlers.RotatingFileHandler(filename=logfile, mode='r', maxBytes=max_logfile_size, backupCount=max_logfile_backups)
        roll.doRollover()
    return

def start_xmlrpc_server():
    """Starts the XMLRPC server in a threaded process."""
    pid = os.getpid()
    try:
        log_rotate()
    except:
        log(format%(pid, '-', '-', 'LOG_ROTATE_ERR', '-', 'Could not rotate logfiles.'))

    try:
        server = MyXMLRPCServer((rpc_host, rpc_port), logRequests=0)
        #server = MyXMLRPCServer((rpc_host, rpc_port), logRequests=1)
        server.register_function(server.shutdown)
        server.register_introspection_functions()
        server.register_instance(VideoIDPool())
        log(format%(pid, '-', '-', 'XMLRPCSERVER', '-', 'Starting XMLRPCServer on port ' + str(rpc_port) + '.'))
        server.serve_forever()
        log(format%(pid, '-', '-', 'XMLRPCSERVER_STOP', '-', 'Stopping XMLRPCServer.'))
    except:
        log(format%(pid, '-', '-', 'STRAT_XMLRPC_SERVER_ERR', '-', 'Cannot start XMLRPC Server - Exiting'))
        os.kill(os.getpid(), 1)
        pass

def download_scheduler():
    """Schedule videos from download queue for downloading."""
    pid = os.getpid()
    log(format%(pid, '-', '-', 'SCHEDULEDER', '-', 'Download Scheduler starting.'))
    time.sleep(random.random()*100%2)
    try:
        video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        if not video_id_pool.set_scheduler(pid):
            return
    except:
        log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', 'Error while querying RPC server (while initializing scheduler).'))

    wait_time = 20
    while True:
        try:
            video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
            params = video_id_pool.schedule()
            if params == False:
                wait_time = 5
            elif params == True:
                wait_time = 0.2
            else:
                try:
                    if params[5] == 'RAPIDSHARE':
                        forked = fork(download_from_rapidshare)
                    else:
                        forked = fork(download_from_source)
                    forked(params)
                    log(format%(pid, params[0], params[4], 'SCHEDULED', params[5], 'Video scheduled for download.'))
                    wait_time = 0.2
                except:
                    remove(video_id)
                    log(format%(pid, '-', '-', 'SCHEDULED_ERR', '-', 'Could not schedule video for download.'))
                    wait_time = 0.5
        except:
            log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', 'Error while querying RPC server.'))
        time.sleep(wait_time)
    log(format%(pid, '-', '-', 'SCHEDULEDER_STOP', '-', 'Download Scheduler stopping.'))
    return

if __name__ == '__main__':
    global log, video_id_pool
    log = set_logging()
    if log is not None:
        # If XMLRPCServer is running already, don't start it again
        try:
            time.sleep(random.random()*100%5)
            video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
            # Flush previous values on reload
            video_id_pool.flush()
            # For testing with squid, use this function
            squid_part()
        except:
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

