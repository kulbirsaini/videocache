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
import logging
import logging.handlers
import os
import random
import re
import stat
import sys
import threading
import time
import urlgrabber
import urllib2
import urlparse
from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer

import socket

mainconf =  readMainConfig(readStartupConfig('/etc/videocache.conf', '/'))

# Gloabl Options
enable_video_cache = int(mainconf.enable_video_cache)
base_dir = mainconf.base_dir
temp_dir = os.path.join(base_dir, mainconf.temp_dir)
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

# Youtube specific options
enable_youtube_cache = int(mainconf.enable_youtube_cache)
youtube_cache_dir = os.path.join(base_dir, mainconf.youtube_cache_dir)
youtube_cache_size = int(mainconf.youtube_cache_size)
max_youtube_video_size = int(mainconf.max_youtube_video_size)
min_youtube_video_size = int(mainconf.min_youtube_video_size)

# Metacafe specific options
enable_metacafe_cache = int(mainconf.enable_metacafe_cache)
metacafe_cache_dir = os.path.join(base_dir, mainconf.metacafe_cache_dir)
metacafe_cache_size = int(mainconf.metacafe_cache_size)
max_metacafe_video_size = int(mainconf.max_metacafe_video_size)
min_metacafe_video_size = int(mainconf.min_metacafe_video_size)

# Dailymotion specific options
enable_dailymotion_cache = int(mainconf.enable_dailymotion_cache)
dailymotion_cache_dir = os.path.join(base_dir, mainconf.dailymotion_cache_dir)
dailymotion_cache_size = int(mainconf.dailymotion_cache_size)
max_dailymotion_video_size = int(mainconf.max_dailymotion_video_size)
min_dailymotion_video_size = int(mainconf.min_dailymotion_video_size)

# Google.com specific options
enable_google_cache = int(mainconf.enable_google_cache)
google_cache_dir = os.path.join(base_dir, mainconf.google_cache_dir)
google_cache_size = int(mainconf.google_cache_size)
max_google_video_size = int(mainconf.max_google_video_size)
min_google_video_size = int(mainconf.min_google_video_size)

# Redtube.com specific options
enable_redtube_cache = int(mainconf.enable_redtube_cache)
redtube_cache_dir = os.path.join(base_dir, mainconf.redtube_cache_dir)
redtube_cache_size = int(mainconf.redtube_cache_size)
max_redtube_video_size = int(mainconf.max_redtube_video_size)
min_redtube_video_size = int(mainconf.min_redtube_video_size)

# Xtube.com specific options
enable_xtube_cache = int(mainconf.enable_xtube_cache)
xtube_cache_dir = os.path.join(base_dir, mainconf.xtube_cache_dir)
xtube_cache_size = int(mainconf.xtube_cache_size)
max_xtube_video_size = int(mainconf.max_xtube_video_size)
min_xtube_video_size = int(mainconf.min_xtube_video_size)

# Vimeo.com specific options
enable_vimeo_cache = int(mainconf.enable_vimeo_cache)
vimeo_cache_dir = os.path.join(base_dir, mainconf.vimeo_cache_dir)
vimeo_cache_size = int(mainconf.vimeo_cache_size)
max_vimeo_video_size = int(mainconf.max_vimeo_video_size)
min_vimeo_video_size = int(mainconf.min_vimeo_video_size)

# Wrzuta.pl specific options
enable_wrzuta_cache = int(mainconf.enable_wrzuta_cache)
wrzuta_cache_dir = os.path.join(base_dir, mainconf.wrzuta_cache_dir)
wrzuta_cache_size = int(mainconf.wrzuta_cache_size)
max_wrzuta_video_size = int(mainconf.max_wrzuta_video_size)
min_wrzuta_video_size = int(mainconf.min_wrzuta_video_size)

# Youporn.com specific options
enable_youporn_cache = int(mainconf.enable_youporn_cache)
youporn_cache_dir = os.path.join(base_dir, mainconf.youporn_cache_dir)
youporn_cache_size = int(mainconf.youporn_cache_size)
max_youporn_video_size = int(mainconf.max_youporn_video_size)
min_youporn_video_size = int(mainconf.min_youporn_video_size)

# Soapbox.msn.com specific options
enable_soapbox_cache = int(mainconf.enable_soapbox_cache)
soapbox_cache_dir = os.path.join(base_dir, mainconf.soapbox_cache_dir)
soapbox_cache_size = int(mainconf.soapbox_cache_size)
max_soapbox_video_size = int(mainconf.max_soapbox_video_size)
min_soapbox_video_size = int(mainconf.min_soapbox_video_size)

# Tube8.com specific options
enable_tube8_cache = int(mainconf.enable_tube8_cache)
tube8_cache_dir = os.path.join(base_dir, mainconf.tube8_cache_dir)
tube8_cache_size = int(mainconf.tube8_cache_size)
max_tube8_video_size = int(mainconf.max_tube8_video_size)
min_tube8_video_size = int(mainconf.min_tube8_video_size)

# Tvuol.uol.com.br specific options
enable_tvuol_cache = int(mainconf.enable_tvuol_cache)
tvuol_cache_dir = os.path.join(base_dir, mainconf.tvuol_cache_dir)
tvuol_cache_size = int(mainconf.tvuol_cache_size)
max_tvuol_video_size = int(mainconf.max_tvuol_video_size)
min_tvuol_video_size = int(mainconf.min_tvuol_video_size)

# Blip.tv specific options
enable_bliptv_cache = int(mainconf.enable_bliptv_cache)
bliptv_cache_dir = os.path.join(base_dir, mainconf.bliptv_cache_dir)
bliptv_cache_size = int(mainconf.bliptv_cache_size)
max_bliptv_video_size = int(mainconf.max_bliptv_video_size)
min_bliptv_video_size = int(mainconf.min_bliptv_video_size)

# Break.com specific options
enable_break_cache = int(mainconf.enable_break_cache)
break_cache_dir = os.path.join(base_dir, mainconf.break_cache_dir)
break_cache_size = int(mainconf.break_cache_size)
max_break_video_size = int(mainconf.max_break_video_size)
min_break_video_size = int(mainconf.min_break_video_size)

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
        else:
            return
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
                #log(format%(pid, str(video_id_pool.get_conn_number()), '-', 'CONN_AVAIL', '-', '-'))
                video_id = self.get_popular()
                if video_id != "NULL" and self.is_active(video_id) == False and self.get_score(video_id) >= hit_threshold:
                    #log(format%(pid, '-', '-', 'INACTIVE', '-', '-'))
                    params = self.get_details(video_id)
                    if params != False:
                        self.set_score(video_id, 0)
                        self.add_conn(video_id)
                        try:
                            log(format%(pid, params[0], params[4], 'SCHEDULED', params[5], 'Video scheduled for download.'))
                            forked = fork(download_from_source)
                            forked(params)
                        except:
                            log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', 'Could not schedule video for download.'))
                            remove(video_id)
                elif self.is_active(video_id) == True:
                    self.set_score(video_id, 0)
                    return False
                else:
                    return False
        except:
            log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', 'Error in schedule function.'))
        return True

    def set_scheduler(self, pid):
        if self.scheduler is None:
            self.scheduler = pid
        else:
            return False
        return True

    def get_scheduler(self):
        return self.scheduler

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

    def get_conn(self):
        """Return a list of currently active connections."""
        return self.active

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
    def __init__(self, *args, **kwargs):
        self.finished = False
        SimpleXMLRPCServer.__init__(self, *args, **kwargs)

    def shutdown(self):
        self.finished = True
        return 1

    def server_bind(self):
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        SimpleXMLRPCServer.server_bind(self)

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
        video_id_pool.remove(video_id)
        video_id_pool.remove_conn(video_id)
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
        client = args[0]
        url = args[1]
        path = args[2]
        mode = args[3]
        video_id = args[4]
        type = args[5]
        max_size = args[6]
        min_size = args[7]
        cache_size = args[8]
        cache_dir = args[9]
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
        download_path = os.path.join(temp_dir, os.path.basename(path))
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

def cache_video(client, url, type, video_id):
    """This function check whether a video is in cache or not. If not, it fetches
    it from the remote source and cache it and also streams it to the client."""
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    global cache_url
    pid = os.getpid()
    mode = 0644
    try:
        if type == 'YOUTUBE':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(youtube_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_youtube_video_size
            min_size = min_youtube_video_size
            cache_size = youtube_cache_size
            cache_dir = youtube_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'METACAFE':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(metacafe_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_metacafe_video_size
            min_size = min_metacafe_video_size
            cache_size = metacafe_cache_size
            cache_dir = metacafe_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'DAILYMOTION':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(dailymotion_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_dailymotion_video_size
            min_size = min_dailymotion_video_size
            cache_size = dailymotion_cache_size
            cache_dir = dailymotion_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'GOOGLE':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(google_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_google_video_size
            min_size = min_google_video_size
            cache_size = google_cache_size
            cache_dir = google_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'REDTUBE':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(redtube_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_redtube_video_size
            min_size = min_redtube_video_size
            cache_size = redtube_cache_size
            cache_dir = redtube_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'XTUBE':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(xtube_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_xtube_video_size
            min_size = min_xtube_video_size
            cache_size = xtube_cache_size
            cache_dir = xtube_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'VIMEO':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(vimeo_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_vimeo_video_size
            min_size = min_vimeo_video_size
            cache_size = vimeo_cache_size
            cache_dir = vimeo_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'WRZUTA':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(wrzuta_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_wrzuta_video_size
            min_size = min_wrzuta_video_size
            cache_size = wrzuta_cache_size
            cache_dir = wrzuta_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'YOUPORN':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(youporn_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_youporn_video_size
            min_size = min_youporn_video_size
            cache_size = youporn_cache_size
            cache_dir = youporn_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'SOAPBOX':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(soapbox_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_soapbox_video_size
            min_size = min_soapbox_video_size
            cache_size = soapbox_cache_size
            cache_dir = soapbox_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'TUBE8':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(tube8_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_tube8_video_size
            min_size = min_tube8_video_size
            cache_size = tube8_cache_size
            cache_dir = tube8_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'TVUOL':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(tvuol_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_tvuol_video_size
            min_size = min_tvuol_video_size
            cache_size = tvuol_cache_size
            cache_dir = tvuol_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'BLIPTV':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(bliptv_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_bliptv_video_size
            min_size = min_bliptv_video_size
            cache_size = bliptv_cache_size
            cache_dir = bliptv_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    try:
        if type == 'BREAK':
            params = urlparse.urlsplit(url)[3]
            path = os.path.join(break_cache_dir, video_id) + '.flv'
            cached_url = os.path.join(cache_url, 'videocache', type.lower())
            max_size = max_break_video_size
            min_size = min_break_video_size
            cache_size = break_cache_size
            cache_dir = break_cache_dir
    except:
        log(format%(pid, client, video_id, 'QUEUE_ERR', type, 'An error occured while queueing the video.'))
        remove(video_id)
        return url

    if os.path.isfile(path):
        remove(video_id)
        log(format%(pid, client, video_id, 'CACHE_HIT', type, 'Video was served from cache.'))
        return redirect + ':' + os.path.join(cached_url, video_id) + '.flv?' + params
    else:
        log(format%(pid, client, video_id, 'CACHE_MISS', type, 'Requested video was not found in cache.'))
        queue(video_id, [client, url, path, mode, video_id, type, max_size, min_size, cache_size, cache_dir])

    return url

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
            host = fragments[1]
            path = fragments[2]
            params = fragments[3]
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
                if host.find('youtube.com') > -1 and path.find('get_video') > -1 and path.find('get_video_info') < 0:
                    arglist = params.split('&')
                    dict = {}
                    for arg in arglist:
                        try:
                            dict[arg.split('=')[0]] = arg.split('=')[1]
                        except:
                            continue
                    if dict.has_key('video_id'):
                        video_id = dict['video_id']
                        type = 'YOUTUBE'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'YOUTUBE', 'Error querying RPC server'))
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', 'YOUTUBE', 'video_id not found in ' + new_url))

            # Youtube videos served via cache.googlevideo.com are handled here.
            # This code has been merged with Google.com videos
            
            # Metacafe.com caching is handled here.
            if enable_metacafe_cache:
                if host.find('v.mccont.com') > -1 and path.find('ItemFiles') > -1:
                    type = 'METACAFE'
                    try:
                        video_id = urllib2.unquote(path).split(' ')[2].split('.')[0]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'METACAFE', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client ,video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'METACAFE', 'Error querying RPC server'))

            # Dailymotion.com caching is handled here.
            if enable_dailymotion_cache:
                if (re.compile('proxy[a-z0-9\-][a-z0-9][a-z0-9][a-z0-9]?\.dailymotion\.com').search(host) or host.find('vid.akm.dailymotion.com') > -1 or host.find('.cdn.dailymotion.com') > -1)  and (path.find('flv') > -1 or path.find('on2') > -1):
                    try:
                        video_id = path.split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'DAILYMOTION', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'DAILYMOTION'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client ,video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'DAILYMOTION', 'Error querying RPC server'))
            
            # Google.com caching is handled here.
            if enable_google_cache:
                if (host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.google\.[a-z][a-z]').search(host)) and (path.find('videoplayback') > -1 or path.find('get_video') > -1) and path.find('get_video_info') < 0:
                    arglist = params.split('&')
                    dict = {}
                    for arg in arglist:
                        try:
                            dict[arg.split('=')[0]] = arg.split('=')[1]
                        except:
                            continue
                    if dict.has_key('video_id'):
                        video_id = dict['video_id']
                    elif dict.has_key('id'):
                        video_id = dict['id']
                    elif dict.has_key('docid'):
                        video_id = dict['docid']
                    else:
                        video_id = None
                    if video_id is not None:
                        type = 'YOUTUBE'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'YOUTUBE', 'Error querying RPC server'))
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', 'YOUTUBE', 'docid not found in ' + new_url))
            
            # Redtube.com caching is handled here.
            if enable_redtube_cache:
                if host.find('dl.redtube.com') > -1 and path.find('.flv') > -1:
                    try:
                        video_id = path.strip('/').split('/')[-1].replace('.flv','')
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'REDTUBE', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'REDTUBE'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'REDTUBE', 'Error querying RPC server'))
            
            # Xtube.com caching is handled here.
            if enable_xtube_cache:
                if re.compile('[0-9a-z][0-9a-z][0-9a-z]?[0-9a-z]?[0-9a-z]?\.xtube\.com').search(host) and path.find('videos/') > -1 and path.find('.flv') > -1 and path.find('Thumb') < 0 and path.find('av_preview') < 0:
                    try:
                        video_id = path.strip('/').split('/')[-1].replace('.flv','')
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'XTUBE', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'XTUBE'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'XTUBE', 'Error querying RPC server'))
            
            # Vimeo.com caching is handled here.
            if enable_vimeo_cache:
                if host.find('bitcast.vimeo.com') > -1 and path.find('vimeo/videos/') > -1 and path.find('.flv') > -1:
                    try:
                        video_id = path.strip('/').split('/')[-1].replace('.flv','')
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'VIMEO', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'VIMEO'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'VIMEO', 'Error querying RPC server'))
            
            # Wrzuta.pl audio file caching is handled here.
            if enable_wrzuta_cache:
                if host.find('va.wrzuta.pl') > -1 and re.compile('wa[0-9][0-9][0-9][0-9]?').search(path) and params.find('type=a') > -1 and params.find('key=') > -1:
                    arglist = params.split('&')
                    dict = {}
                    for arg in arglist:
                        try:
                            dict[arg.split('=')[0]] = arg.split('=')[1]
                        except:
                            continue
                    if dict.has_key('key'):
                        video_id = dict['key']
                        type = 'WRZUTA'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'WRZUTA', 'Error querying RPC server'))
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', 'WRZUTA', 'key not found in ' + new_url))
            
            # Youporn.com audio file caching is handled here.
            if enable_youporn_cache:
                if host.find('.files.youporn.com') > -1 and path.find('/flv/') > -1 and path.find('.flv') > -1:
                    try:
                        video_id = path.strip('/').split('/')[-1].split('.')[0]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'YOUPORN', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'YOUPORN'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'YOUPORN', 'Error querying RPC server'))
            
            # Soapbox.msn.com audio file caching is handled here.
            if enable_soapbox_cache:
                if host.find('.msn.com.edgesuite.net') > -1 and path.find('.flv') > -1:
                    try:
                        video_id = path.strip('/').split('/')[-1].split('.')[0]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'SOAPBOX', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'SOAPBOX'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'SOAPBOX', 'Error querying RPC server'))
            
            # Tube8.com Video file caching is handled here.
            if enable_tube8_cache:
                if re.compile('media[a-z0-9]?[a-z0-9]?[a-z0-9]?\.tube8\.com').search(host) and (path.find('.flv') > -1 or path.find('.3gp') > -1):
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'TUBE8', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'TUBE8'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'TUBE8', 'Error querying RPC server'))
            
            # Tvuol.uol.com.br Video file caching is handled here.
            if enable_tvuol_cache:
                if host.find('mais.uol.com.br') > -1 and path.find('.flv') > -1:
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'TVUOL', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'TVUOL'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'TVUOL', 'Error querying RPC server'))
            
            # Blip.tv Video file caching is handled here.
            if enable_bliptv_cache:
                if re.compile('\.video[a-z0-9]?[a-z0-9]?\.blip\.tv').search(host) and (path.find('.flv') > -1 or path.find('.wmv') > -1 or path.find('.mp4') > -1 or path.find('.rm') > -1 or path.find('.ram') > -1 or path.find('.mov') > -1 or path.find('.avi') > -1 or path.find('.m4v') > -1 or path.find('.mp3') > -1) :
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'BLIPTV', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'BLIPTV'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'BLIPTV', 'Error querying RPC server'))
            
            # Break.com Video file caching is handled here.
            if enable_break_cache:
                if host.find('video.break.com') > -1 and (path.find('.flv') > -1 or path.find('.mp4')):
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except:
                        log(format%(pid, client, '-', 'URL_ERROR', 'BREAK', 'Error in parsing the url ' + new_url))
                        video_id = None
                    if video_id is not None:
                        type = 'BREAK'
                        try:
                            videos = video_id_pool.get()
                            if video_id in videos:
                                video_id_pool.inc_score(video_id)
                                pass
                            else:
                                video_id_pool.add(video_id)
                                log(format%(pid, client, video_id, 'URL_HIT', type, url[0]))
                                new_url = cache_video(client, url[0], type, video_id)
                                log(format%(pid, client, video_id, 'NEW_URL', type, new_url))
                        except:
                            log(format%(pid, client, video_id, 'XMLRPC_ERR', 'BREAK', 'Error querying RPC server'))
            
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
            if video_id_pool.schedule() == False:
                wait_time = 15
            else:
                wait_time = 1
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
            #list = video_id_pool.get()
            # Flush previous values on reload
            video_id_pool.flush()
            # For testing with squid, use this function
            squid_part()
        except:
            # Start XMLRPC Server, Download Scheduler and Base Plugin in threads.
            thread_xmlrpc = Function_Thread(XMLRPC_SERVER)
            thread_download_scheduler = Function_Thread(DOWNLOAD_SCHEDULER)
            #thread_base_plugin = Function_Thread(BASE_PLUGIN)
            thread_xmlrpc.start()
            thread_download_scheduler.start()
            #thread_base_plugin.start()
            thread_xmlrpc.join()
            thread_download_scheduler.join()
            #thread_base_plugin.join()

