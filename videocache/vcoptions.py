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

from vcconfig import VideocacheConfig

import logging
import logging.handlers
import os
import traceback
import urlparse

class VideocacheOptions:
    initialized = False
    halt = True

    def __init__(self, config_file = '/etc/videocache.conf', root = '/'):
        self.config_file = config_file
        self.root = root
        self.youtube_format = { '240p' : [5], '360p' : [34, 18, 43], '480p' : [35], '720p' : [22, 45], '1080p' : [37], '3072p' : [38] }
        self.youtube_format_order = [ '240p', '360p', '480p', '720p', '1080p', '3072p' ]
        self.websites = ['youtube', 'aol', 'bing', 'bliptv', 'breakcom', 'cnn', 'dailymotion', 'facebook', 'megavideo', 'metacafe', 'myspace', 'vimeo', 'wrzuta', 'extremetube', 'hardsextube', 'keezmovies', 'pornhub', 'redtube', 'slutload', 'spankwire', 'tube8', 'xhamster', 'xtube', 'xvideos', 'youporn']
        self.__class__.trace_logformat = '%(localtime)s %(process_id)s %(client_ip)s %(website_id)s %(code)s %(video_id)s\n%(message)s'
        self.format_map = { '%ts' : '%(timestamp)s', '%tu' : '%(timestamp_ms)s', '%tl' : '%(localtime)s', '%tg' : '%(gmt_time)s', '%p' : '%(process_id)s', '%s' : '%(levelname)s', '%i' : '%(client_ip)s', '%w' : '%(website_id)s', '%c' : '%(code)s', '%v' : '%(video_id)s', '%b' : '%(size)s', '%m' : '%(message)s', '%d' : '%(debug)s' }
        self.arg_drop_list = {'youtube': [], 'aol': [], 'bing': [], 'bliptv': ['start'], 'breakcom': ['ec_seek'], 'cnn': [], 'dailymotion': ['start'], 'facebook': [], 'megavideo': [], 'metacafe': [], 'myspace': [], 'vimeo': [], 'wrzuta': [], 'extremetube': ['start'], 'hardsextube': ['start'], 'keezmovies': ['start'], 'pornhub': ['start'], 'redtube': [], 'slutload': ['ec_seek'], 'spankwire': ['start'], 'tube8': ['start'], 'xhamster': ['start'], 'xtube': ['start'], 'xvideos': ['fs'], 'youporn': ['fs']}
        return self.initialize()

    def initialize(self):
        if self.__class__.initialized:
            return

        try:
            mainconf =  VideocacheConfig(self.config_file, self.root).read()
        except Exception, e:
            syslog_msg('Could not read configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None

        try:
            # Options not in configuration file
            self.__class__.queue_dump_file = mainconf.queue_dump_file
            self.__class__.version = '1.9.9'
            # General Options
            self.__class__.enable_videocache = int(mainconf.enable_videocache)
            self.__class__.enable_videocache_cleaner = int(mainconf.enable_videocache_cleaner)
            self.__class__.video_lifetime = int(mainconf.video_lifetime)
            self.__class__.offline_mode = int(mainconf.offline_mode)
            self.__class__.videocache_user = mainconf.videocache_user
            self.__class__.videocache_group = mainconf.videocache_group
            self.__class__.max_cache_processes = int(mainconf.max_cache_processes)
            self.__class__.hit_threshold = int(mainconf.hit_threshold)
            self.__class__.max_video_size = int(mainconf.max_video_size) * 1024 * 1024
            self.__class__.min_video_size = int(mainconf.min_video_size) * 1024 * 1024
            self.__class__.client_email = mainconf.client_email
            self.__class__.cache_periods = cache_period_s2lh(mainconf.cache_period)
            self.__class__.max_cache_queue_size = int(mainconf.max_cache_queue_size)
            self.__class__.info_server = mainconf.info_server
            self.__class__.video_server = mainconf.video_server
            self.__class__.squid_store_log = mainconf.squid_store_log
            self.__class__.ssl_fo = None

            # Filesystem
            self.__class__.base_dir_list = [dir.strip() for dir in mainconf.base_dir.split('|')]
            self.__class__.temp_dir = mainconf.temp_dir
            self.__class__.base_dir_selection = int(mainconf.base_dir_selection)
            self.__class__.disk_avail_threshold = int(mainconf.disk_avail_threshold)

            # Logging
            self.__class__.logdir = mainconf.logdir
            self.__class__.timeformat = mainconf.timeformat
            self.__class__.scheduler_pidfile = mainconf.scheduler_pidfile
            # Mail Videocache Logfile
            self.__class__.enable_videocache_log = int(mainconf.enable_videocache_log)
            self.__class__.logformat = mainconf.logformat
            self.__class__.logfile = os.path.join(mainconf.logdir, mainconf.logfile)
            self.__class__.max_logfile_size = int(mainconf.max_logfile_size) * 1024 * 1024
            self.__class__.max_logfile_backups = int(mainconf.max_logfile_backups)
            # Trace file
            self.__class__.enable_trace_log = int(mainconf.enable_trace_log)
            self.__class__.tracefile = os.path.join(mainconf.logdir, mainconf.tracefile)
            self.__class__.max_tracefile_size = int(mainconf.max_tracefile_size) * 1024 * 1024
            self.__class__.max_tracefile_backups = int(mainconf.max_tracefile_backups)
            # Scheduler Logfile
            self.__class__.enable_scheduler_log = int(mainconf.enable_scheduler_log)
            self.__class__.scheduler_logformat = mainconf.scheduler_logformat
            self.__class__.scheduler_logfile = os.path.join(mainconf.logdir, mainconf.scheduler_logfile)
            self.__class__.max_scheduler_logfile_size = int(mainconf.max_scheduler_logfile_size) * 1024 * 1024
            self.__class__.max_scheduler_logfile_backups = int(mainconf.max_scheduler_logfile_backups)
            # Videocache Cleaner Logfile
            self.__class__.enable_cleaner_log = int(mainconf.enable_cleaner_log)
            self.__class__.cleaner_logformat = mainconf.cleaner_logformat
            self.__class__.cleaner_logfile = os.path.join(mainconf.logdir, mainconf.cleaner_logfile)
            self.__class__.max_cleaner_logfile_size = int(mainconf.max_cleaner_logfile_size) * 1024 * 1024
            self.__class__.max_cleaner_logfile_backups = int(mainconf.max_cleaner_logfile_backups)

            # Network
            self.__class__.cache_host = str(mainconf.cache_host).strip()
            self.__class__.rpc_host = mainconf.rpc_host
            self.__class__.rpc_port = int(mainconf.rpc_port)
            proxy = mainconf.proxy
            proxy_username = mainconf.proxy_username
            proxy_password = mainconf.proxy_password
            self.__class__.max_cache_speed = int(mainconf.max_cache_speed) * 1024
            self.__class__.id = ''

            # Other
            self.__class__.pid = os.getpid()
        except Exception, e:
            syslog_msg('Could not load options from configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None

        # Website specific options
        try:
            [ (setattr(self.__class__, 'enable_' + website_id + '_cache', int(eval('mainconf.enable_' + website_id + '_cache'))), setattr(self.__class__, website_id + '_cache_dir', eval('mainconf.' + website_id + '_cache_dir'))) for website_id in self.websites ]
            valid_youtube_formats = self.youtube_format_order[:self.youtube_format_order.index(mainconf.max_youtube_video_quality) + 1]
            self.__class__.youtube_video_formats = []
            [self.__class__.youtube_video_formats.extend(self.youtube_format[i]) for i in valid_youtube_formats]
            self.__class__.youtube_video_formats.reverse()
            self.__class__.min_youtube_views = int(mainconf.min_youtube_views)
        except Exception, e:
            syslog_msg('Could not set website specific options. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # Create a list of cache directories available
        try:
            base_dirs = {}
            for website_id in self.websites:
                base_dirs[website_id] = [os.path.join(dir, eval('self.__class__.' + website_id + '_cache_dir')) for dir in self.__class__.base_dir_list]
            base_dirs['tmp'] = [os.path.join(dir, self.__class__.temp_dir) for dir in self.__class__.base_dir_list]
            self.__class__.base_dirs = base_dirs
        except Exception, e:
            syslog_msg('Could not build a list of cache directories. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        try:
            self.__class__.cache_url = 'http://' + self.__class__.cache_host + '/'
            cache_host_parts = self.__class__.cache_host.split(':')
            if len(cache_host_parts) == 1:
                self.__class__.cache_host_ip = cache_host_parts[0]
                self.__class__.cache_host_port = 80
            elif len(cache_host_parts) == 2:
                self.__class__.cache_host_ip = cache_host_parts[0]
                self.__class__.cache_host_port = int(cache_host_parts[1])
            else:
                self.__class__.cache_host_ip = None
                self.__class__.cache_host_port = None
        except Exception, e:
            syslog_msg('Could not generate Cache URL for serving videos from cache. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        try:
            self.__class__.rpc_url = 'http://' + self.__class__.rpc_host + ':' + str(self.__class__.rpc_port)
        except Exception, e:
            syslog_msg('Could not generate RPC URL for XMLRPC communication. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        try:
            self.__class__.proxy = None
            if proxy:
                if proxy_username and proxy_password:
                    proxy_parts = urlparse.urlsplit(proxy)
                    self.__class__.proxy = '%s://%s:%s@%s/' % (proxy_parts[0], proxy_username, proxy_password, proxy_parts[1])
                else:
                    self.__class__.proxy = proxy
        except Exception, e:
            syslog_msg('Could not set proxy for caching videos. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # HTTP Headers for caching videos
        self.__class__.redirect_code = '302'
        self.__class__.std_headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language': 'en-us,en;q=0.5',
        }

        self.__class__.initialized = True
        self.__class__.halt = False

    def set_loggers(self):
        # Set loggers
        try:
            for key in self.format_map:
                self.__class__.logformat = self.__class__.logformat.replace(key, self.format_map[key])
                self.__class__.scheduler_logformat = self.__class__.scheduler_logformat.replace(key, self.format_map[key])
                self.__class__.cleaner_logformat = self.__class__.cleaner_logformat.replace(key, self.format_map[key])
            # Main Videocache Logfile
            if self.__class__.enable_videocache_log:
                self.__class__.vc_logger = logging.Logger('VideocacheLog')
                self.__class__.vc_logger.setLevel(logging.DEBUG)
                vc_log_handler = logging.handlers.RotatingFileHandler(self.__class__.logfile, mode = 'a', maxBytes = self.__class__.max_logfile_size, backupCount = self.__class__.max_logfile_backups)
                self.__class__.vc_logger.addHandler(vc_log_handler)

            # Scheduler Logfile
            if self.__class__.enable_scheduler_log:
                self.__class__.vcs_logger = logging.Logger('VideocacheSchedulerLog')
                self.__class__.vcs_logger.setLevel(logging.DEBUG)
                vcs_log_handler = logging.handlers.RotatingFileHandler(self.__class__.scheduler_logfile, mode = 'a', maxBytes = self.__class__.max_scheduler_logfile_size, backupCount = self.__class__.max_scheduler_logfile_backups)
                self.__class__.vcs_logger.addHandler(vcs_log_handler)

            # Trace log
            if self.__class__.enable_trace_log:
                self.__class__.trace_logger = logging.Logger('VideocacheTraceLog')
                self.__class__.trace_logger.setLevel(logging.DEBUG)
                trace_log_handler = logging.handlers.RotatingFileHandler(self.__class__.tracefile, mode = 'a', maxBytes = self.__class__.max_tracefile_size, backupCount = self.__class__.max_tracefile_backups)
                self.__class__.trace_logger.addHandler(trace_log_handler)

            # Videocache Cleaner Logfile
            if self.__class__.enable_cleaner_log:
                self.__class__.vcc_logger = logging.Logger('VideocacheCleanerLog')
                self.__class__.vcc_logger.setLevel(logging.DEBUG)
                vcc_log_handler = logging.handlers.RotatingFileHandler(self.__class__.cleaner_logfile, mode = 'a', maxBytes = self.__class__.max_cleaner_logfile_size, backupCount = self.__class__.max_cleaner_logfile_backups)
                self.__class__.vcc_logger.addHandler(vcc_log_handler)

        except Exception, e:
            syslog_msg('Could not set logging! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None
        return True

    def reset(self):
        self.__class__.initialized = False
        self.initialize()

