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
# For configuration and how to use, see README file.
#

__author__ = """Kulbir Saini <kulbirsaini@students.iiit.ac.in>"""
__version__ = 0.1
__docformat__ = 'plaintext'

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from config import readMainConfig, readStartupConfig
import logging
import logging.handlers
import md5
import os
import stat
import sys
import urlgrabber
import urllib2
import urlparse
from xmlrpclib import ServerProxy
from SimpleXMLRPCServer import SimpleXMLRPCServer

mainconf =  readMainConfig(readStartupConfig('/etc/youtube_cache.conf', '/'))

# Gloabl Options
base_dir = mainconf.base_dir
temp_dir = os.path.join(base_dir, mainconf.temp_dir)
cache_host = mainconf.cache_host
rpc_host = mainconf.rpc_host
rpc_port = int(mainconf.rpc_port)
logfile = mainconf.logfile
max_logfile_size = int(mainconf.max_logfile_size) * 1024 * 1024
max_logfile_backups = int(mainconf.max_logfile_backups)
proxy = mainconf.proxy
proxy_username = mainconf.proxy_username
proxy_password = mainconf.proxy_password

redirect = '303'
format = '%s %s %s %s %s'
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

def set_proxy():
    if proxy_username and proxy_password:
        proxy_parts = urlparse.urlsplit(proxy)
        new_proxy = '%s://%s:%s@%s/' % (proxy_parts[0], proxy_username, proxy_password, proxy_parts[1])
    else:
        new_proxy = proxy
    return urlgrabber.grabber.URLGrabber(proxies = {'http': new_proxy})

def set_logging():
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(levelname)s %(message)s',
                        filename=logfile,
                        filemode='a')
    return logging.info

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

class Bucket:
    """
    This class is for sharing the current packages being downloading
    across various instances of intelligentmirror via XMLRPC.
    """
    def __init__(self, packages = []):
        self.packages = packages
        pass

    def get(self):
        return self.packages

    def set(self, packages):
        self.packages = packages
        return self.packages

    def add(self, package):
        if package not in self.packages:
            self.packages.append(package)
        return self.packages

    def remove(self, package):
        if package in self.packages:
            self.packages.remove(package)
        return self.packages

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

def remove(query):
    packages = bucket.get()
    md5id = md5.md5(query).hexdigest()
    bucket.remove(md5id)

def download_from_source(client, url, path, mode, video_id, type, max_size, min_size):
    """This function downloads the file from remote source and caches it."""
    if max_size or min_size:
        try:
            log(format%(client, video_id, 'GET_SIZE', type, 'Trying to get the size of video.'))
            remote_file = grabber.urlopen(url)
            remote_size = int(remote_file.info().getheader('content-length')) / 1024
            remote_file.close()
            log(format%(client, video_id, 'GOT_SIZE', type, 'Successfully retrieved the size of video.'))
        except urlgrabber.grabber.URLGrabError, e:
            log(format%(client, video_id, 'SIZE_ERR', type, 'Could not retrieve size of the video.'))
            return

        if max_size and remote_size > max_size:
            log(format%(client, video_id, 'MAX_SIZE', type, 'Video size ' + str(remote_size) + ' is larger than maximum allowed.'))
            return
        if min_size and remote_size < min_size:
            log(format%(client, video_id, 'MIN_SIZE', type, 'Video size ' + str(remote_size) + ' is smaller than minimum allowed.'))
            return

    try:
        download_path = os.path.join(temp_dir, md5.md5(os.path.basename(path)).hexdigest())
        open(download_path, 'a').close()
        file = grabber.urlgrab(url, download_path)
        os.rename(file, path)
        os.chmod(path, mode)
        remove(video_id)
        size = os.stat(path)[6]
        log(format%(client, video_id, 'DOWNLOAD', type, str(size) + ' Video was downloaded and cached.'))
    except urlgrabber.grabber.URLGrabError, e:
        remove(video_id)
        log(format%(client, video_id, 'DOWNLOAD_ERR', type, 'An error occured while retrieving the video.'))
        os.unlink(download_path)

    return

def cache_video(client, url, type, video_id):
    """This function check whether a video is in cache or not. If not, it fetches
    it from the remote source and cache it and also streams it to the client."""
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    global cache_url
    mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    if type == 'YOUTUBE':
        params = urlparse.urlsplit(url)[3]
        path = os.path.join(youtube_cache_dir, video_id) + '.flv'
        cached_url = os.path.join(cache_url, base_dir.strip('/').split('/')[-1], type.lower())
        max_size = max_youtube_video_size
        min_size = min_youtube_video_size
        cache_size = youtube_cache_size
        cache_dir = youtube_cache_dir

    if type == 'METACAFE':
        params = urlparse.urlsplit(url)[3]
        path = os.path.join(metacafe_cache_dir, video_id) + '.flv'
        cached_url = os.path.join(cache_url, base_dir.strip('/').split('/')[-1], type.lower())
        max_size = max_metacafe_video_size
        min_size = min_metacafe_video_size
        cache_size = metacafe_cache_size
        cache_dir = metacafe_cache_dir

    if type == 'DAILYMOTION':
        params = urlparse.urlsplit(url)[3]
        path = os.path.join(dailymotion_cache_dir, video_id) + '.flv'
        cached_url = os.path.join(cache_url, base_dir.strip('/').split('/')[-1], type.lower())
        max_size = max_dailymotion_video_size
        min_size = min_dailymotion_video_size
        cache_size = dailymotion_cache_size
        cache_dir = dailymotion_cache_dir

    if type == 'GOOGLE':
        params = urlparse.urlsplit(url)[3]
        path = os.path.join(google_cache_dir, video_id) + '.flv'
        cached_url = os.path.join(cache_url, base_dir.strip('/').split('/')[-1], type.lower())
        max_size = max_google_video_size
        min_size = min_google_video_size
        cache_size = google_cache_size
        cache_dir = google_cache_dir

    if os.path.isfile(path):
        log(format%(client, video_id, 'CACHE_HIT', type, 'Requested video was found in cache.'))
        cur_mode = os.stat(path)[stat.ST_MODE]
        remove(video_id)
        if stat.S_IMODE(cur_mode) == mode:
            log(format%(client, video_id, 'CACHE_SERVE', type, 'Video was served from cache.'))
            return redirect + ':' + os.path.join(cached_url, video_id) + '.flv?' + params
    elif cache_size == 0 or dir_size(cache_dir) < cache_size:
        log(format%(client, video_id, 'CACHE_MISS', type, 'Requested video was not found in cache.'))
        forked = fork(download_from_source)
        forked(client, url, path, mode, video_id, type, max_size, min_size)
    else:
        log(format%(client, video_id, 'CACHE_FULL', type, 'Cache directory \'' + cache_dir + '\' has exceeded the maximum size allowed.'))

    return url

def squid_part():
    """This function will tap requests from squid. If the request is for a youtube
    video, they will be forwarded to function cache_video() for further processing.
    Finally this function will flush a cache_url if package found in cache or a
    blank line in case on a miss to stdout. This is the only function where we deal
    with squid, rest of the program/project doesn't interact with squid at all."""
    while True:
        # Read url from stdin ( this is provided by squid)
        url = sys.stdin.readline().strip().split(' ')
        new_url = url[0];
        # Retrieve the basename from the request url
        fragments = urlparse.urlsplit(url[0])
        host = fragments[1]
        path = fragments[2]
        params = fragments[3]
        client = url[1].split('/')[0]
        log(format%(client, '-', 'REQUEST', '-', url[0]))
        # Youtube.com caching is handled here.
        if enable_youtube_cache:
            if host.find('youtube.com') > -1 and path.find('get_video') > -1:
                video_id = params.split('&')[0].split('=')[1]
                type = 'YOUTUBE'
                md5id = md5.md5(video_id).hexdigest()
                videos = bucket.get()
                if md5id in videos:
                    pass
                else:
                    bucket.add(md5id)
                    log(format%(client, video_id, 'URL_HIT', type, url[0]))
                    new_url = cache_video(client, url[0], type, video_id)
                    log(format%(client, video_id, 'NEW_URL', type, new_url))
        
        # Metacafe.com caching is handled here.
        if enable_metacafe_cache:
            if host.find('v.mccont.com') > -1 and path.find('ItemFiles') > -1:
                type = 'METACAFE'
                video_id = urllib2.unquote(path).split(' ')[2].split('.')[0]
                md5id = md5.md5(video_id).hexdigest()
                videos = bucket.get()
                if md5id in videos:
                    pass
                else:
                    bucket.add(md5id)
                    log(format%(client ,video_id, 'URL_HIT', type, url[0]))
                    new_url = cache_video(client, url[0], type, video_id)
                    log(format%(client, video_id, 'NEW_URL', type, new_url))

        # Dailymotion.com caching is handled here.
        if enable_dailymotion_cache:
            if host.find('dailymotion.com') > -1 and host.find('proxy') > -1 and path.find('on2') > -1:
                video_id = path.split('/')[-1]
                type = 'DAILYMOTION'
                md5id = md5.md5(video_id).hexdigest()
                videos = bucket.get()
                if md5id in videos:
                    pass
                else:
                    bucket.add(md5id)
                    log(format%(client, video_id, 'URL_HIT', type, url[0]))
                    new_url = cache_video(client, url[0], type, video_id)
                    log(format%(client ,video_id, 'NEW_URL', type, new_url))
        
        # Google.com caching is handled here.
        if enable_google_cache:
            if host.find('vp.video.google.com') > -1 and path.find('videodownload') > -1:
                video_id = params.split('&')[-1].split('=')[-1]
                type = 'GOOGLE'
                md5id = md5.md5(video_id).hexdigest()
                videos = bucket.get()
                if md5id in videos:
                    pass
                else:
                    bucket.add(md5id)
                    log(format%(client, video_id, 'URL_HIT', type, url[0]))
                    new_url = cache_video(client, url[0], type, video_id)
                    log(format%(client, video_id, 'NEW_URL', type, new_url))
        
        # Flush the new url to stdout for squid to process
        sys.stdout.write(new_url + '\n')
        sys.stdout.flush()

if __name__ == '__main__':
    global grabber, log, bucket
    grabber = set_proxy()
    log = set_logging()

    # If XMLRPCServer is running already, don't start it again
    try:
        bucket = ServerProxy('http://' + rpc_host + ':' + str(rpc_port))
        list = bucket.get()
    except:
        server = SimpleXMLRPCServer((rpc_host, rpc_port))
        server.register_instance(Bucket())
        log(format%('-', '-', 'XMLRPCServer', '-', 'Starting XMLRPCServer on port ' + str(rpc_port) + '.'))
        # Rotate logfiles it the size is more than the max_logfile_size.
        if os.stat(logfile)[6] > max_logfile_size:
            roll = logging.handlers.RotatingFileHandler(filename=logfile, mode='r', maxBytes=max_logfile_size, backupCount=max_logfile_backups)
            roll.doRollover()
        server.serve_forever()

    # For testing with squid, use this function
    squid_part()

