#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from cache import *
from common import *
from error_codes import *
from vcdaemon import VideocacheDaemon
from vcoptions import VideocacheOptions

from optparse import OptionParser
from rpyc.utils.server import ThreadedServer

import logging
import pwd
import rpyc
import sys
import threading
import time
import traceback

def info(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.INFO)})
    o.vcs_logger.info(build_message(params))

def error(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.ERROR)})
    o.vcs_logger.error(build_message(params))

def warn(params = {}):
    params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.WARN)})
    o.vcs_logger.debug(build_message(params))

def trace(params = {}):
    params.update({ 'trace_logformat' : o.trace_logformat, 'timeformat' : o.timeformat })
    o.trace_logger.info(build_trace(params))

class VideoPool(rpyc.Service):
    """
    This class is for sharing the current packages being downloading
    across various instances of Videocache via RPC.
    """
    scores = {}
    queue = {}
    active = []
    time_threshold = 8
    scheduler = None

    def on_connect(self):
        pass

    def on_disconnect(self):
        pass

    def exposed_get_active_videos(self):
        return self.active

    def exposed_get_video_scores(self):
        return self.scores

    def exposed_get_video_queue(self):
        return self.queue

    def exposed_add_videos(self, video_pool = {}):
        """
        New videos are added to the queue and there scores are set to 0.
        If a video is already queued, its score is incremented by 1.
        """
        info( { 'code' : VIDEOS_RECEIVED, 'message' : 'Received ' + str(len(video_pool)) + ' videos from Videocache.' } )
        for video_id in video_pool:
            if video_id in self.queue:
                self.add_video(video_id, video_pool[video_id])
            else:
                self.queue[video_id] = video_pool[video_id]
                self.scores[video_id] = 1
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

            try:
                self.queue[video_id].update( { 'urls' : list(set(old_data['urls'] + params['urls'])) } )
            except Exception, e:
                pass
        return True

    def get_score(self, video_id):
        """Get the score of video represented by video_id."""
        if video_id in self.scores:
            return self.scores[video_id]
        else:
            return 0

    def exposed_set_score(self, video_id, score = 1):
        """Set the priority score of a video_id."""
        if video_id in self.scores:
            self.scores[video_id] = score
        return True

    def inc_score(self, video_id, incr = 1):
        """Increase the priority score of video represented by video_id."""
        if video_id in self.scores:
            self.scores[video_id] += incr
        return True

    def exposed_dec_score(self, video_id, decr = 1):
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

    def exposed_remove_from_queue(self, video_id):
        """Dequeue a video_id from the download queue."""
        if video_id in self.queue:
            self.queue.pop(video_id)
        if video_id in self.scores:
            self.scores.pop(video_id)
        return True

    def exposed_remove_url_from_queue(self, video_id, url):
        """Dequeue a url for a video_id from the download queue."""
        if video_id in self.queue:
            if url in self.queue[video_id]['urls']:
                self.queue[video_id]['urls'].remove(url)
        return True

    def exposed_remove(self, video_id):
        """Remove video_id from queue as well as active connection list."""
        return self.exposed_remove_from_queue(video_id) and self.remove_conn(video_id)

    def exposed_remove_url(self, video_id, url):
        """Remove url from url list for a video_id."""
        if len(self.queue[video_id]['urls']) == 1:
            return self.exposed_remove(video_id)
        else:
            return self.exposed_remove_url_from_queue(video_id, url)

    def exposed_flush(self):
        """Flush the queue and reinitialize everything."""
        self.queue = {}
        self.scores = {}
        self.active = []
        return True

    def exposed_schedule(self):
        """Returns the parameters for a video to be downloaded from remote."""
        try:
            if self.get_conn_number() < self.o.max_cache_processes:
                video_id = self.get_popular()
                if video_id != False and self.is_active(video_id) == False and self.get_score(video_id) >= self.o.hit_threshold:
                    params = self.get_details(video_id)
                    if params != False:
                        self.exposed_set_score(video_id, 0)
                        self.add_conn(video_id)
                        return params
                elif self.is_active(video_id) == True:
                    self.exposed_set_score(video_id, 0)
                    return False
                else:
                    return False
            else:
                return False
        except Exception, e:
            pass
        return True

    def set_scheduler(self, pid):
        if self.scheduler is None:
            self.scheduler = pid
            return True
        return False

    # Functions related download scheduling.
    # Have to mess up things in single class because python
    # RPCServer doesn't allow to register multiple instances.
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
        return video_id in self.active

    def remove_conn(self, video_id):
        """Remove video_id from active connections list."""
        if video_id in self.active:
            self.active.remove(video_id)
        return True

class VideoPoolDaemon(VideocacheDaemon):

    def __init__(self, o = None, **kwargs):
        self.o = o
        VideocacheDaemon.__init__(self, o.scheduler_pidfile, **kwargs)

    def run(self):
        try:
            self.o.set_loggers()
            server = ThreadedServer(VideoPool, hostname = self.o.rpc_host, port = self.o.rpc_port)
            info( { 'code' : VIDEO_POOL_SERVER_START, 'message' : 'Starting VideoPool Server at port ' + str(self.o.rpc_port) + '.' } )
            server.start()
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

