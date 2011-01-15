#!/usr/bin/env python

#
# (C) Copyright 2008-2010 Kulbir Saini <saini@saini.co.in>
# (C) Copyright 2008-2010 Videocache Pvt Ltd.
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <kulbirsaini@students.iiit.ac.in>"""
__docformat__ = 'plaintext'

from config import readMainConfig, readStartupConfig
from optparse import OptionParser
from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer
import cgi
import logging
import logging.handlers
import os
import random
import re
import socket
import statvfs
import sys
import syslog
import threading
import time
import traceback
import urlgrabber
import urllib
import urllib2
import urlparse

def syslog_msg(msg):
    syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, msg)

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
            if self.get_conn_number() < max_cache_processes:
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
        if proxy:
            if proxy_username and proxy_password:
                proxy_parts = urlparse.urlsplit(proxy)
                new_proxy = '%s://%s:%s@%s/' % (proxy_parts[0], proxy_username, proxy_password, proxy_parts[1])
            else:
                new_proxy = proxy
            return urlgrabber.grabber.URLGrabber(user_agent = user_agent, proxies = {'http': new_proxy}, http_headers = http_headers, keepalive = 1)
        else:
            return urlgrabber.grabber.URLGrabber(user_agent = user_agent, http_headers = http_headers, keepalive = 1)
    except Exception, e:
        log(format%(os.getpid(), '-', '-', 'PROXY_ERR', '-', str(e)))
        return None

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

def video_params_all((base_path, base_path_size), video_id, type, url, index = ''):
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

def download_from_source(args):
    """This function downloads the file from remote source and caches it."""
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    mode = 0644
    pid = os.getpid()
    try:
        [client, urls, video_id, type] = [i for i in args]
    except Exception, e:
        log(format%(pid, '-', '-', 'SCHEDULE_ERR', '-', str(e)))
        return

    index = None
    for base_tup in base_dir:
        # Pick up cache directories one by one.
        try:
            (path, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params_all(base_tup, video_id, type, urls, base_dir.index(base_tup))
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
        (path, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params_all(base_dir[index], video_id, type, urls, index)
    else:
        # No idea what went wrong.
        remove(video_id)
        return

    grabber = set_proxy()
    if grabber is None:
        remove(video_id)
        return

    if False: #if max_size or min_size:
        try:
            log(format%(pid, client, video_id, 'GET_SIZE', type, 'Trying to get the size of video.'))
            remote_file = grabber.urlopen(url)
            remote_size = int(remote_file.info().getheader('content-length')) / 1024
            remote_file.close()
            log(format%(pid, client, video_id, 'GOT_SIZE', type, str(remote_size) + ' Successfully retrieved the size of video.'))
        except Exception, e:
            remove(video_id)
            log(format%(pid, client, video_id, 'SIZE_ERR', type, str(e)))
            return

        if max_size and remote_size > max_size:
            remove(video_id)
            log(format%(pid, client, video_id, 'MAX_SIZE', type, 'Video size ' + str(remote_size) + ' is larger than maximum allowed.'))
            return
        if min_size and remote_size < min_size:
            remove(video_id)
            log(format%(pid, client, video_id, 'MIN_SIZE', type, 'Video size ' + str(remote_size) + ' is smaller than minimum allowed.'))
            return

    for url in urls:
        original_url = url
        url = refine_url(url, ['begin', 'start', 'noflv'])
        try:
            try:
                new_path = new_url = None
                if type == 'YOUTUBE':
                    try:
                        url_obj = grabber.urlopen(url)
                        new_url = url_obj.fo.geturl()
                        url_obj.close()
                    except urlgrabber.grabber.URLGrabError, http_error:
                        try:
                            log(format%(pid, client, video_id, 'ALTERNATE_URL_OPEN_ERR', type, 'HTTP ERROR : ' + str(http_error.code) + ' : An error occured while retrieving the alternate video id.  ' + url))
                        except:
                            log(format%(pid, client, video_id, 'ALTERNATE_URL_OPEN_ERR', type, 'HTTP ERROR : ' + str(http_error) + ' : An error occured while retrieving the alternate video id.  ' + url))
                    except Exception, e:
                        log(format%(pid, client, video_id, 'ALTERNATE_URL_ERR', type, str(e)))
                    if new_url is not None and url != new_url:
                        new_video_id = get_new_video_id(new_url)
                        (new_path, max_size, min_size, cache_size, cache_dir, tmp_cache) = video_params_all(base_dir[index], new_video_id, type, urls, index)
                        if os.path.exists(new_path):
                            os.link(new_path, path)
                            os.utime(path, None)
                            os.utime(new_path, None)
                            log(format%(pid, client, video_id, 'DOWNLOAD_LINK', type, ' Video was linked to another cached video.'))
                            remove(video_id)
                            return
            except Exception, e:
                log(format%(pid, client, video_id, 'ALTERNATE_PATH_ERR', type, str(e)))
            download_path = os.path.join(tmp_cache, os.path.basename(path))
            open(download_path, 'a').close()
            file = grabber.urlgrab(url, download_path)
            size = os.path.getsize(file)
            os.rename(file, path)
            os.chmod(path, mode)
            os.utime(path, None)
            try:
                if new_path is not None:
                    if not os.path.exists(new_path):
                        os.link(path, new_path)
                    os.utime(new_path, None)
            except Exception, e:
                log(format%(pid, client, video_id, 'ALTERNATE_LINK_ERR', type, str(e)))
            remove(video_id)
            log(format%(pid, client, video_id, 'DOWNLOAD', type, str(size) + ' Video was downloaded and cached.'))
            return
        except urlgrabber.grabber.URLGrabError, http_error:
            if urls.index(original_url) == len(urls) - 1:
                remove(video_id)
            try:
                log(format%(pid, client, video_id, 'DOWNLOAD_HTTP_ERR', type, 'HTTP ERROR : ' + str(http_error.code) + ' : An error occured while retrieving the video.  '  + url))
            except:
                log(format%(pid, client, video_id, 'DOWNLOAD_HTTP_ERR', type, 'HTTP ERROR : ' + str(http_error) + ' : An error occured while retrieving the video.  '  + url))
        except Exception, e:
            if urls.index(original_url) == len(urls) - 1:
                remove(video_id)
            log(format%(pid, client, video_id, 'DOWNLOAD_ERR', type, str(e)))

    return

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
            return redirect + ':' + refine_url(url, ['noflv'])

    if not cache_check_only:
        log(format%(pid, client, video_id, 'CACHE_MISS', type, 'Requested video was not found in cache.'))
        # Queue video using daemon forking as it'll save time in returning the url.
        forked = fork(queue)
        forked(video_id, [client, [url], video_id, type])
    return url

def submit_video(pid, client, type, url, video_id, cache_check_only = False):
    return ''
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
    input = sys.stdin.readline()
    while input:
        new_url = ''
        skip = False
        try:
            # Read url from stdin (this is provided by squid)
            fields = input.strip().split(' ')
            if len(fields) < 4:
                # Log that fields from squid were corrupt
                skip = True
            elif fields[3].upper() != 'GET':
                # Can't handle this request
                skip = True
            else:
                url = fields[0]
                client = fields[1].split('/')[0]
                # Retrieve the basename from the request url
                fragments = urlparse.urlsplit(fields[0])
                if len(fragments) < 4:
                    # Not a proper URL
                    skip = True
                else:
                    [host, path, query] = [fragments[1], fragments[2], fragments[3]]
        except Exception, e:
            # Error in parsnig data from squid
            skip = True

        # Check if videocache plugin is on.
        if not skip and enable_videocache:
            matched = False
            # Youtube.com ang Google Video caching is handled here.
            if not matched and enable_youtube_cache:
                if (path.find('get_video') > -1) and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.youtube\.[a-z][a-z]').search(host) or re.compile('\.youtube\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host)):
                    type = 'YOUTUBE'
                    matched = True
                    dict = cgi.parse_qs(query)
                    if dict.has_key('video_id'):
                        video_id = dict['video_id'][0]
                    elif dict.has_key('docid'):
                        video_id = dict['docid'][0]
                    elif dict.has_key('id'):
                        video_id = dict['id'][0]
                    else:
                        video_id = None

                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'Video ID not found in ' + new_url))

            # Youtube.com and Google Video caching is handled here. URLs to videoplayback.
            if not matched and enable_google_cache:
                if (path.find('videoplayback') > -1 or path.find('videoplay') > -1) and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.google.com') > -1 or host.find('.googlevideo.com') > -1 or re.compile('\.youtube\.[a-z][a-z]').search(host) or re.compile('\.youtube\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]').search(host) or re.compile('\.google\.[a-z][a-z]\.[a-z][a-z]').search(host) or re.compile('^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$').match(host)):
                    type = 'YOUTUBE'
                    matched = True
                    dict = cgi.parse_qs(query)
                    if dict.has_key('video_id'):
                        video_id = dict['video_id'][0]
                    elif dict.has_key('docid'):
                        video_id = dict['docid'][0]
                    elif dict.has_key('id'):
                        video_id = dict['id'][0]
                    else:
                        video_id = None

                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id, True)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'docid not found in ' + new_url))

            # Metacafe.com caching is handled here.
            if not matched and enable_metacafe_cache:
                if (host.find('.mccont.com') > -1 or host.find('akvideos.metacafe.com') > -1 ) and path.find('ItemFiles') > -1:
                    type = 'METACAFE'
                    matched = True
                    try:
                        video_id = urllib2.unquote(path).strip('/').split(' ')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None

                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Dailymotion.com caching is handled here.
            if not matched and enable_dailymotion_cache:
                if (path.find('.flv') > -1 or path.find('.on2') > -1 or path.find('.mp4') > -1) and (host.find('vid.akm.dailymotion.com') > -1 or host.find('.cdn.dailymotion.com') > -1 or re.compile('proxy[a-z0-9\-][a-z0-9][a-z0-9][a-z0-9]?\.dailymotion\.com').search(host)):
                    type = 'DAILYMOTION'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Redtube.com caching is handled here.
            if not matched and enable_redtube_cache:
                if host.find('.redtube.com') > -1 and path.find('.flv') > -1:
                    type = 'REDTUBE'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Xtube.com caching is handled here.
            if not matched and enable_xtube_cache:
                if path.find('videos/') > -1 and path.find('.flv') > -1 and path.find('Thumb') < 0 and path.find('av_preview') < 0 and re.compile('[0-9a-z][0-9a-z][0-9a-z]?[0-9a-z]?[0-9a-z]?\.xtube\.com').search(host):
                    type = 'XTUBE'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Vimeo.com caching is handled here.
            if not matched and enable_vimeo_cache:
                if host.find('bitcast.vimeo.com') > -1 and path.find('vimeo/videos/') > -1 and path.find('.flv') > -1:
                    type = 'VIMEO'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Wrzuta.pl audio file caching is handled here.
            if not matched and enable_wrzuta_cache:
                if host.find('va.wrzuta.pl') > -1 and query.find('type=a') > -1 and query.find('key=') > -1 and re.compile('wa[0-9][0-9][0-9][0-9]?').search(path):
                    type = 'WRZUTA'
                    matched = True
                    dict = cgi.parse_qs(query)
                    if dict.has_key('key'):
                        video_id = dict['key'][0]
                        new_url = submit_video(pid, client, type, url, video_id)
                    else:
                        log(format%(pid, client, '-', 'URL_ERROR', type, 'key not found in ' + new_url))

            # Youporn.com caching is handled here.
            if not matched and enable_youporn_cache:
                if host.find('.files.youporn.com') > -1 and path.find('/flv/') > -1 and path.find('.flv') > -1:
                    type = 'YOUPORN'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Soapbox.msn.com caching is handled here.
            if not matched and enable_soapbox_cache:
                if host.find('.msn.com.edgesuite.net') > -1 and path.find('.flv') > -1:
                    type = 'SOAPBOX'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Tube8.com Video file caching is handled here.
            if not matched and enable_tube8_cache:
                if (path.find('.flv') > -1 or path.find('.3gp') > -1) and (re.compile('media[a-z0-9]?[a-z0-9]?[a-z0-9]?\.tube8\.com').search(host) or re.compile('mobile[a-z0-9]?[a-z0-9]?[a-z0-9]?\.tube8\.com').search(host)):
                    type = 'TUBE8'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Tvuol.uol.com.br Video file caching is handled here.
            if not matched and enable_tvuol_cache:
                if host.find('mais.uol.com.br') > -1 and path.find('.flv') > -1:
                    type = 'TVUOL'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Blip.tv Video file caching is handled here.
            if not matched and enable_bliptv_cache:
                if re.compile('\.video[a-z0-9]?[a-z0-9]?\.blip\.tv').search(host) and (path.find('.flv') > -1 or path.find('.wmv') > -1 or path.find('.mp4') > -1 or path.find('.rm') > -1 or path.find('.ram') > -1 or path.find('.mov') > -1 or path.find('.avi') > -1 or path.find('.m4v') > -1 or path.find('.mp3') > -1):
                    type = 'BLIPTV'
                    matched = True
                    try:
                        video_id = path.strip('/').split('/')[-1]
                    except Exception, e:
                        log(format%(pid, client, '-', 'URL_ERROR', type, str(e) + ' : ' + new_url))
                        video_id = None
                    if video_id is not None:
                        new_url = submit_video(pid, client, type, url, video_id)

            # Break.com Video file caching is handled here.
            if not matched and enable_break_cache:
                if host.find('video.break.com') > -1 and (path.find('.flv') > -1 or path.find('.mp4')):
                    type = 'BREAK'
                    matched = True
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
        except Exception, e:
            # Could not write back to Squid
            log('Could not write back to Squid')
        input = sys.stdin.readline()
    else:
        # Log that exiting
        log('Exiting')
        # squid_part
        pass

def start_xmlrpc_server():
    """Starts the XMLRPC server in a threaded process."""
    pid = os.getpid()
    try:
        server = MyXMLRPCServer((rpc_host, rpc_port), logRequests=0)
        server.register_function(server.shutdown)
        server.register_introspection_functions()
        server.register_instance(VideoIDPool())
        log(format%(pid, '-', '-', 'XMLRPCSERVER', '-', 'Starting XMLRPCServer on port ' + str(rpc_port) + '.'))
        server.serve_forever()
        log(format%(pid, '-', '-', 'XMLRPCSERVER_STOP', '-', 'Stopping XMLRPCServer.'))
    except Exception, e:
        #log(format%(pid, '-', '-', 'START_XMLRPC_SERVER_ERR', '-', 'Cannot start XMLRPC Server - Exiting'))
        os.kill(pid, 1)
        pass

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

# Parse command line options.
parser = OptionParser()
parser.add_option('--home')
parser.add_option('--prefix')
parser.add_option('--install-root')
options, args = parser.parse_args()

try:
    root = '/'
    if options.home:
        root = options.home
    elif options.prefix:
        root = options.prefix
    elif options.install_root:
        root = options.install_root
    mainconf =  readMainConfig(readStartupConfig('/etc/videocache.conf', root))
except Exception, e:
    syslog_msg('Code: 001. Message: Could not load configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
    halt = True

# Gloabl Options
format_map = { '%ts' : '%(timestamp)s', '%tu' : '%(timestamp_ms)s', '%tl' : '%(localtime)s', '%tg' : '%(gmt_time)s', '%p' : '%(process)d', '%s' : '%(levelname)s', '%i' : '%(client_ip)s', '%w' : '%(website_id)s', '%c' : '%(code)s', '%v' : '%(video_id)s', '%m' : '%(message)s', '%d' : '%(lineno)d %(debug)s', '%b' : '%(trace)s' }
try:
    # General Options
    enable_videocache = int(mainconf.enable_videocache)
    offline_mode = int(mainconf.offline_mode)
    max_cache_processes = int(mainconf.max_cache_processes)
    hit_threshold = int(mainconf.hit_threshold)
    max_video_size = int(mainconf.max_video_size) * 1024 * 1024
    min_video_size = int(mainconf.min_video_size) * 1024 * 1024

    # Filesystem
    base_dir_list = mainconf.base_dir.split('|')
    temp_dir = mainconf.temp_dir
    disk_avail_threshold = int(mainconf.disk_avail_threshold)
    logfile = os.path.join(mainconf.logdir, 'videocache.log')
    max_logfile_size = int(mainconf.max_logfile_size) * 1024 * 1024
    max_logfile_backups = int(mainconf.max_logfile_backups)
    logformat = mainconf.logformat

    # Network
    cache_host = mainconf.cache_host
    rpc_host = mainconf.rpc_host
    rpc_port = int(mainconf.rpc_port)
    proxy = mainconf.proxy
    proxy_username = mainconf.proxy_username
    proxy_password = mainconf.proxy_password
except Exception, e:
    syslog_msg('Code: 002. Message: Could not load options from configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
    halt = True

# Set loggers
try:
    for key in format_map:
        logformat = logformat.replace(key, format_map[key])
    logger = logging.Logger('VideocacheLog')
    logger.setLevel(logging.DEBUG)
    handler = logging.handlers.RotatingFileHandler(logfile, mode = 'a', maxBytes = max_logfile_size, backupCount = max_logfile_backups)
    #handler.setFormatter(logging.Formatter(logformat))
    #logger.addHandler(handler)
    info = logger.info
    debug = logger.debug
    error = logger.error
    warn = logger.warn
except Exception, e:
    syslog_msg('Code: 006. Message: Could not set logging! Debug: '  + traceback.format_exc().replace('\n', ''))
    halt = True

# Threading
BASE_PLUGIN = 0
XMLRPC_SERVER = 1
DOWNLOAD_SCHEDULER = 2

# HTTP Headers for caching videos
redirect = '302'
format = '%s %s %s %s %s %s'
user_agent = 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 GTB6'
http_headers = (
    ('Proxy-CONNECTION', 'keep-alive'),
    ('ACCEPT', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
)
try:
    cache_url = 'http://' + str(cache_host) + '/'
except Exception, e:
    syslog_msg('Code: 003. Message: Could not set cache host for serving cached videos! Debug: '  + traceback.format_exc().replace('\n', ''))
    halt = True

# Create a list of cache directories available
try:
    base_dir = []
    for dir in base_dir_list:
        try:
            dir_tup = [val.strip() for val in dir.split(':')]
            if len(dir_tup) == 1 or (len(dir_tup) == 2 and dir_tup[1] == ''):
                base_dir.append((dir_tup[0], 0))
            elif len(dir_tup) == 2:
                base_dir.append((dir_tup[0], int(dir_tup[1])))
        except Exception, e:
            pass
except Exception, e:
    syslog_msg('Code: 004. Message: Could not build a list of cache directories! Debug: '  + traceback.format_exc().replace('\n', ''))
    halt = True

# Set website specific options
def set_globals(type_low):
    enable_cache = int(eval('mainconf.enable_' + type_low + '_cache'))
    cache_dir = eval('mainconf.' + type_low + '_cache_dir')
    return (enable_cache, cache_dir)

# Website specific options
try:
    [(enable_youtube_cache, youtube_cache_dir), (enable_metacafe_cache, metacafe_cache_dir), (enable_dailymotion_cache, dailymotion_cache_dir), (enable_google_cache, google_cache_dir), (enable_redtube_cache, redtube_cache_dir), (enable_xtube_cache, xtube_cache_dir), (enable_vimeo_cache, vimeo_cache_dir), (enable_wrzuta_cache, wrzuta_cache_dir), (enable_youporn_cache, youporn_cache_dir), (enable_soapbox_cache, soapbox_cache_dir), (enable_tube8_cache, tube8_cache_dir), (enable_tvuol_cache, tvuol_cache_dir), (enable_bliptv_cache, bliptv_cache_dir), (enable_break_cache, break_cache_dir)] = [ set_globals(website_id) for website_id in ['youtube', 'metacafe', 'dailymotion', 'google', 'redtube', 'xtube', 'vimeo', 'wrzuta', 'youporn', 'soapbox', 'tube8', 'tvuol', 'bliptv', 'break'] ]
except Exception, e:
    syslog_msg('Code: 005. Message: Could not set website specific options! Debug: '  + traceback.format_exc().replace('\n', ''))
    halt = True

# FIXME To be removed
logging.basicConfig(level=logging.DEBUG,
       format='%(asctime)s %(message)s',
       filename=logfile,
       filemode='a')
log = logging.info


if __name__ == '__main__':
    try:
        if halt:
            syslog_msg('Code: 007. Message: Could not start videocache. Please check syslog for errors! Debug: '  + traceback.format_exc().replace('\n', ''))
            sys.exit(1)
    except Exception, e:
        pass

    syslog_msg('Starting videocache!')
    # If XMLRPCServer is running already, don't start it again
    try:
        squid_part()
    except:
        log(traceback.format_exc())
    #try:
    #    #time.sleep(random.random()*100%7)
    #    #video_id_pool = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
    #    # Flush previous values on reload
    #    #video_id_pool.flush()
    #    # For testing with squid, use this function
    #except Exception, e:
    #    print 'could not start squid part'
    #    # Start XMLRPC Server, Download Scheduler and Base Plugin in threads.
    #    #thread_xmlrpc = Function_Thread(XMLRPC_SERVER)
    #    #thread_download_scheduler = Function_Thread(DOWNLOAD_SCHEDULER)
    #    thread_base_plugin = Function_Thread(BASE_PLUGIN)
    #    #thread_xmlrpc.start()
    #    #thread_download_scheduler.start()
    #    thread_base_plugin.start()
    #    #thread_xmlrpc.join()
    #    #thread_download_scheduler.join()
    #    thread_base_plugin.join()

