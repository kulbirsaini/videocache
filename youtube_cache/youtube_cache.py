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
import md5
import os
import rfc822
import stat
import sys
import time
import urlgrabber
import urlparse

mainconf =  readMainConfig(readStartupConfig('/etc/youtube_cache.conf', '/'))

# cache_dir => Directory where squid this program will cache the youtube videos.
cache_dir = mainconf.cache_dir + '/'
# cachce_host => Hostname or IP Address of the caching server.
cache_host = mainconf.cache_host
# temp_dir => Directory to download packages temporarily
temp_dir = mainconf.temp_dir + '/'
# logfile => Location where this program will log the actions.
logfile = mainconf.logfile
# http_proxy => The proxy to use for http requests.
http_proxy = mainconf.http_proxy
# http_port => The port to use dummy http server.
http_port = mainconf.http_port

cache_url = 'http://' + str(cache_host) + ':' + str(http_port) + '/' 

redirect = '303'
format = '%-12s %-12s %s'

logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=logfile,
                    filemode='a')
log = logging.info

grabber = urlgrabber.grabber.URLGrabber(proxies = {'http': http_proxy})

class HTTPHandler(BaseHTTPRequestHandler):
    """
    Class to serve youtube videos via python webserver.
    """
    def do_GET(self):
        try:
            if self.path.endswith(".flv"):
                f = open(cache_dir + '/' + self.path)
                self.send_response(200)
                self.send_header('Content-type', 'video/x-flv')
                self.end_headers()
                self.wfile.write(f.read())
                f.close()
                return
        except IOError:
            self.send_error(404,'File Not Found: %s' % self.path)

# If python webserver is running already, it won't be started again.
try:
    server = HTTPServer(('', int(http_port)), HTTPHandler)
    log(format%('-'*11, 'HTTP_SERVER', 'Starting python web server on port ' + str(http_port)))
    server.serve_forever()
except:
    pass

def fork(f):
    """This function is highly inspired from concurrency in python
    tutorial at http://blog.buffis.com/?p=63 .
    Generator for creating a forked process from a function"""
    # Perform double fork
    r = ''
    if os.fork(): # Parent
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

def download_from_source(url, path, mode):
    """This function downloads the file from remote source and caches it."""
    try:
        download_path = os.path.join(temp_dir, md5.md5(os.path.basename(path)).hexdigest())
        open(download_path, 'a').close()
        file = grabber.urlgrab(url, download_path)
        os.rename(file, path)
        os.chmod(path, mode)
        log(format%(os.path.basename(path).split('.')[0], 'DOWNLOAD', 'Package was downloaded and cached.'))
    except urlgrabber.grabber.URLGrabError, e:
        log(format%(video_id, 'URL_ERROR', 'An error occured while retrieving the package.'))

def cache_video(url):
    """This function check whether a video is in cache or not. If not, it fetches
    it from the remote source and cache it and also streams it to the client."""
    # The expected mode of the cached file, so that it is readable by apache
    # to stream it to the client.
    mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH
    params = urlparse.urlsplit(url)[3]
    video_id = params.split('&')[0].split('=')[1]
    video = cache_dir + video_id + '.flv'
    if os.path.isfile(video):
        log(format%(video_id, 'CACHE_HIT', 'Requested package was found in cache.'))
        cur_mode = os.stat(video)[stat.ST_MODE]
        if stat.S_IMODE(cur_mode) == mode:
            log(format%(video_id, 'CACHE_SERVE', 'Package was served from cache.'))
            return redirect + ':' + cache_url + video_id + '.flv'
    elif os.path.isfile(os.path.join(temp_dir, md5.md5(os.path.basename(video)).hexdigest())):
        log(format%(video_id, 'INCOMPLETE', 'Video is still being downloaded.'))
        return ''
    else:
        log(format%(video_id, 'CACHE_MISS', 'Requested package was not found in cache.'))
        forked = fork(download_from_source)
        forked(url, video, mode)
        return ''
    return '' 

def squid_part():
    """This function will tap requests from squid. If the request is for a youtube
    video, they will be forwarded to function cache_video() for further processing.
    Finally this function will flush a cache_url if package found in cache or a
    blank line in case on a miss to stdout. This is the only function where we deal
    with squid, rest of the program/project doesn't interact with squid at all."""
    while True:
        # Read url from stdin ( this is provided by squid)
        url = sys.stdin.readline().strip().split(' ')
        new_url = '\n';
        # Retrieve the basename from the request url
        fragments = urlparse.urlsplit(url[0])
        host = fragments[1]
        path = fragments[2]
        if host.find('youtube.com') > -1 and path.find('get_video') > -1:
            log(format%('-'*11, 'URL_HIT', 'Request for ' + url[0]))
            new_url = cache_video(url[0]) + new_url
            log(format%('-'*11, 'NEW_URL', new_url.strip('\n')))
        # Flush the new url to stdout for squid to process
        sys.stdout.write(new_url)
        sys.stdout.flush()

def cmd_squid_part():
    """This function will tap requests from squid. If the request is for a youtube
    video, they will be forwarded to function cache_video() for further processing.
    Finally this function will flush a cache_url if package found in cache or a
    blank line in case on a miss to stdout. This is the only function where we deal
    with squid, rest of the program/project doesn't interact with squid at all."""
    while True:
        # Read url from stdin ( this is provided by squid)
        url = sys.argv[1].strip().split(' ')
        new_url = '\n';
        # Retrieve the basename from the request url
        fragments = urlparse.urlsplit(url[0])
        host = fragments[1]
        path = fragments[2]
        if host.find('youtube.com') > -1 and path.find('get_video') > -1:
            log(format%('-'*11, 'URL_HIT', 'Request for ' + url[0]))
            new_url = cache_video(url[0]) + new_url
        # Flush the new url to stdout for squid to process
        print 'new_url:', new_url.strip()
        break

if __name__ == '__main__':
    # For testing with squid, use this function
    squid_part()
    # For testing on command line, use this function
    #cmd_squid_part()

