#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *
from fsop import create_dir
from store import partition_size
from vcconfig import VideocacheConfig

from cloghandler import ConcurrentRotatingFileHandler
from logging.handlers import BaseRotatingHandler

import logging
import logging.handlers
import os
import traceback
import urlparse

class MyConcurrentRotatingFileHandler(ConcurrentRotatingFileHandler):
    def __init__(self, filename, mode='a', maxBytes=0, backupCount=0,
                 encoding=None, debug=True, supress_abs_warn=False):
        try:
            BaseRotatingHandler.__init__(self, filename, mode, encoding)
        except TypeError: # Due to a different logging release without encoding support  (Python 2.4.1 and earlier?)
            BaseRotatingHandler.__init__(self, filename, mode)
            self.encoding = encoding

        self._rotateFailed = False
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        # Prevent multiple extensions on the lock file (Only handles the normal "*.log" case.)
        lock_dir = os.path.join(os.path.dirname(filename), '.lock')
        if not os.path.isdir(lock_dir):
            create_dir(lock_dir)
        log_filename = os.path.basename(filename)
        if log_filename.endswith(".log"):
            lock_file = os.path.join(lock_dir, log_filename[:-4])
        else:
            lock_file = os.path.join(lock_dir, log_filename)
        self.stream_lock = open(lock_file + ".lock", "w")

        # For debug mode, swap out the "_degrade()" method with a more a verbose one.
        if debug:
            self._degrade = self._degrade_debug

class VideocacheOptions:
    loggers_set = False
    initialized = False
    halt = True
    config_file = None
    generate_crossdomain_files = False
    skip_disk_size_calculation = False

    def __init__(self, config_file = '/etc/videocache.conf', generate_crossdomain_files = False, skip_disk_size_calculation = False):
        self.__class__.config_file = config_file
        self.__class__.generate_crossdomain_files = generate_crossdomain_files
        self.__class__.skip_disk_size_calculation = skip_disk_size_calculation
        self.__class__.initialize(config_file, generate_crossdomain_files, skip_disk_size_calculation)

    @classmethod
    def initialize(klass, config_file, generate_crossdomain_files = False, skip_disk_size_calculation = False):
        if klass.initialized:
            return

        klass.youtube_res_order = [144, 224, 270, 360, 480, 720, 520, 540, 1080, 2304]
        klass.youtube_itag_order = { 'regular' : ['38', '37', '22', '35', '34', '6', '5'], 'regular_3d' : ['84', '85', '82', '83'], 'webm' : ['46', '45', '44', '43'], 'webm_3d' : ['102', '101', '100'], '3gp' : ['17', '13'], 'mobile' : ['18'] }
        klass.youtube_itag_groups = [ ['5', '6'], ['13', '17'], ['22', '37'], ['34', '35'], ['82', '83'], ['84', '85'], ['43', '44'], ['45', '46'], ['100', '101'] ]
        klass.youtube_audio_only_itags = [ '140', '141' ]
        klass.youtube_video_only_itags = [ '137', '136', '135', '134', '133', '160' ]
        klass.youtube_skip_caching_itags = [ '140', '141', '137', '136', '135', '134', '133', '160' ]
        klass.youtube_formats = {
            '5'   : {'res': 224,  'ext': '.flv',  'cat': 'regular'},
            '6'   : {'res': 270,  'ext': '.flv',  'cat': 'regular'},
            '13'  : {'res': 144,  'ext': '.3gp',  'cat': '3gp'},
            '17'  : {'res': 144,  'ext': '.3gp',  'cat': '3gp'},
            '18'  : {'res': 360,  'ext': '.mp4',  'cat': 'mobile'},
            '34'  : {'res': 360,  'ext': '.flv',  'cat': 'regular'},
            '35'  : {'res': 480,  'ext': '.flv',  'cat': 'regular'},
            '22'  : {'res': 720,  'ext': '.mp4',  'cat': 'regular'},
            '37'  : {'res': 1080, 'ext': '.mp4',  'cat': 'regular'},
            '38'  : {'res': 2304, 'ext': '.mp4',  'cat': 'regular'},
            '83'  : {'res': 240,  'ext': '.mp4',  'cat': 'regular_3d'},
            '82'  : {'res': 360,  'ext': '.mp4',  'cat': 'regular_3d'},
            '85'  : {'res': 520,  'ext': '.mp4',  'cat': 'regular_3d'},
            '84'  : {'res': 720,  'ext': '.mp4',  'cat': 'regular_3d'},
            '43'  : {'res': 360,  'ext': '.webm', 'cat': 'webm'},
            '44'  : {'res': 480,  'ext': '.webm', 'cat': 'webm'},
            '45'  : {'res': 720,  'ext': '.webm', 'cat': 'webm'},
            '46'  : {'res': 1080, 'ext': '.webm', 'cat': 'webm'},
            '100' : {'res': 360,  'ext': '.webm', 'cat': 'webm_3d'},
            '101' : {'res': 480,  'ext': '.webm', 'cat': 'webm_3d'},
            '102' : {'res': 720,  'ext': '.webm', 'cat': 'webm_3d'},
            '133' : {'res': 240,  'ext': '.mp4',  'cat': 'regular'},
            '134' : {'res': 360,  'ext': '.mp4',  'cat': 'regular'},
            '135' : {'res': 480,  'ext': '.mp4',  'cat': 'regular'},
            '136' : {'res': 720,  'ext': '.mp4',  'cat': 'regular'},
            '137' : {'res': 1080, 'ext': '.mp4',  'cat': 'regular'},
            '160' : {'res': 144,  'ext': '.mp4',  'cat': 'regular'},
            '140' : {'res': 480,  'ext': '.mp4',  'cat': 'regular'},
            '141' : {'res': 480,  'ext': '.mp4',  'cat': 'regular'},
        }

        klass.websites = ['android', 'youtube', 'aol', 'bing', 'bliptv', 'breakcom', 'dailymotion', 'facebook', 'imdb', 'metacafe', 'myspace', 'veoh', 'videobash', 'vimeo', 'vube', 'weather', 'wrzuta', 'youku', 'extremetube', 'hardsextube', 'keezmovies', 'pornhub', 'redtube', 'slutload', 'spankwire', 'tube8', 'xhamster', 'xtube', 'xvideos', 'youporn']
        klass.trace_logformat = '%(localtime)s %(process_id)s %(client_ip)s %(website_id)s %(code)s %(video_id)s\n%(message)s'
        klass.format_map = { '%ts' : '%(timestamp)s', '%tu' : '%(timestamp_ms)s', '%tl' : '%(localtime)s', '%tg' : '%(gmt_time)s', '%p' : '%(process_id)s', '%s' : '%(levelname)s', '%i' : '%(client_ip)s', '%w' : '%(website_id)s', '%c' : '%(code)s', '%v' : '%(video_id)s', '%b' : '%(size)s', '%m' : '%(message)s', '%d' : '%(debug)s' }
        klass.arg_drop_list = {'android' : [], 'youtube': ['noflv', 'begin'], 'aol': ['timeoffset', 'set', 'aktimeoffset'], 'bing': [], 'bliptv': ['start'], 'breakcom': ['ec_seek'], 'dailymotion': ['start'], 'facebook': [], 'imdb' : [], 'metacafe': [], 'myspace': [], 'veoh' : ['ms'], 'videobash' : ['start'], 'vimeo': ['aktimeoffset'], 'vube' : [], 'weather': [], 'wrzuta': ['sec-offset'], 'youku': ['start', 'preview_ts', 'preview_num'], 'extremetube': ['start'], 'hardsextube': ['start'], 'keezmovies': ['start'], 'pornhub': ['start', 'fs', 'ms'], 'redtube': ['ec_seek'], 'slutload': ['ec_seek'], 'spankwire': ['start'], 'tube8': ['start', 'ms'], 'xhamster': ['start'], 'xtube': ['start', 'fs', 'ms'], 'xvideos': ['fs'], 'youporn': ['fs', 'ms']}

        try:
            mainconf =  VideocacheConfig(config_file).read()
        except Exception, e:
            syslog_msg('Could not read configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None

        try:
            # Options not in configuration file
            klass.queue_dump_file = mainconf.queue_dump_file
            klass.version = '2.3'
            klass.revision = 'g1306a29'
            # General Options
            klass.enable_videocache = int(mainconf.enable_videocache)
            klass.offline_mode = int(mainconf.offline_mode)
            klass.videocache_user = mainconf.videocache_user
            klass.videocache_group = mainconf.videocache_group
            klass.max_cache_processes = int(mainconf.max_cache_processes)
            klass.hit_threshold = int(mainconf.hit_threshold)
            klass.max_video_size = int(mainconf.max_video_size) * 1048576
            klass.min_video_size = int(mainconf.min_video_size) * 1048576
            klass.force_video_size = int(mainconf.force_video_size)
            klass.client_email = mainconf.client_email
            klass.cache_periods = cache_period_s2lh(mainconf.cache_period)
            klass.info_server = mainconf.info_server
            klass.video_server = mainconf.video_server
            klass.this_proxy = mainconf.this_proxy.strip()
            klass.enable_access_log_monitoring = int(mainconf.enable_access_log_monitoring)
            klass.squid_access_log = mainconf.squid_access_log
            klass.file_mode = 0644
            klass.db_hostname = mainconf.db_hostname
            klass.db_username = mainconf.db_username
            klass.db_password = mainconf.db_password
            klass.db_database = mainconf.db_database
            klass.cpn_lifetime = 1800
            klass.video_queue_lifetime = int(mainconf.video_queue_lifetime)
            klass.active_queue_lifetime = int(mainconf.active_queue_lifetime)
            klass.tmp_file_lifetime = int(mainconf.tmp_file_lifetime)
            klass.hit_time_threshold = int(mainconf.hit_time_threshold)
            klass.log_hit_threshold = int(mainconf.log_hit_threshold)
            klass.max_queue_size_per_plugin = int(mainconf.max_queue_size_per_plugin)
            klass.max_log_hit_monitor_queue_size = int(mainconf.max_log_hit_monitor_queue_size)
            klass.access_log_read_timeout = int(mainconf.access_log_read_timeout)
            klass.socket_read_block_size = int(mainconf.socket_read_block_size)
            klass.trial = int(mainconf.trial)
            if klass.trial:
                klass.trial = 1

            # Apache
            klass.skip_apache_conf = int(mainconf.skip_apache_conf)
            klass.apache_conf_dir = mainconf.apache_conf_dir.strip()
            klass.hide_cache_dirs = int(mainconf.hide_cache_dirs)

            # Filesystem
            klass.base_dir = mainconf.base_dir
            klass.base_dir_list = [dir.strip() for dir in mainconf.base_dir.split('|')]
            klass.temp_dir = mainconf.temp_dir.strip('/').split('/')[-1]
            klass.base_dir_selection = int(mainconf.base_dir_selection)
            klass.disk_cleanup_strategy = int(mainconf.disk_cleanup_strategy)
            if klass.disk_cleanup_strategy == 2:
                klass.cleanup_order = 'size DESC, access_count ASC, access_time ASC'
            elif klass.disk_cleanup_strategy == 3:
                klass.cleanup_order = 'access_time ASC, access_count ASC, size DESC'
            else:
                klass.cleanup_order = 'access_count ASC, access_time ASC, size DESC'
            klass.filelist_rebuild_interval = int(mainconf.filelist_rebuild_interval)
            cache_swap_low = min(max(int(mainconf.cache_swap_low), 85), 98)
            cache_swap_high = min(max(int(mainconf.cache_swap_high), 90), 99)
            if cache_swap_low > cache_swap_high:
                cache_swap_low, cache_swap_high = cache_swap_high, cache_swap_low
            elif cache_swap_low == cache_swap_high:
                cache_swap_low -= 1
            klass.cache_swap_low = cache_swap_low
            klass.cache_swap_high = cache_swap_high

            # Logging
            klass.logdir = mainconf.logdir
            klass.timeformat = mainconf.timeformat
            klass.pidfile = mainconf.pidfile
            klass.pidfile_path = os.path.join(mainconf.logdir, '.lock', mainconf.pidfile)
            # Mail Videocache Logfile
            klass.enable_videocache_log = int(mainconf.enable_videocache_log)
            klass.logformat = mainconf.logformat
            klass.logfile = mainconf.logfile
            klass.logfile_path = os.path.join(mainconf.logdir, mainconf.logfile)
            klass.max_logfile_size = int(mainconf.max_logfile_size)
            klass.max_logfile_size_in_bytes = int(mainconf.max_logfile_size) * 1048576
            klass.max_logfile_backups = int(mainconf.max_logfile_backups)
            # Trace file
            klass.enable_trace_log = int(mainconf.enable_trace_log)
            klass.tracefile = mainconf.tracefile
            klass.tracefile_path = os.path.join(mainconf.logdir, mainconf.tracefile)
            klass.max_tracefile_size = int(mainconf.max_tracefile_size)
            klass.max_tracefile_size_in_bytes = int(mainconf.max_tracefile_size) * 1048576
            klass.max_tracefile_backups = int(mainconf.max_tracefile_backups)
            # Scheduler Logfile
            klass.enable_scheduler_log = int(mainconf.enable_scheduler_log)
            klass.scheduler_logformat = mainconf.scheduler_logformat
            klass.scheduler_logfile = mainconf.scheduler_logfile
            klass.scheduler_logfile_path = os.path.join(mainconf.logdir, mainconf.scheduler_logfile)
            klass.max_scheduler_logfile_size = int(mainconf.max_scheduler_logfile_size)
            klass.max_scheduler_logfile_size_in_bytes = int(mainconf.max_scheduler_logfile_size) * 1048576
            klass.max_scheduler_logfile_backups = int(mainconf.max_scheduler_logfile_backups)
            # Videocache Cleaner Logfile
            klass.enable_cleaner_log = int(mainconf.enable_cleaner_log)
            klass.cleaner_logformat = mainconf.cleaner_logformat
            klass.cleaner_logfile = mainconf.cleaner_logfile
            klass.cleaner_logfile_path = os.path.join(mainconf.logdir, mainconf.cleaner_logfile)
            klass.max_cleaner_logfile_size = int(mainconf.max_cleaner_logfile_size)
            klass.max_cleaner_logfile_size_in_bytes = int(mainconf.max_cleaner_logfile_size) * 1048576
            klass.max_cleaner_logfile_backups = int(mainconf.max_cleaner_logfile_backups)
            # DB Logfile
            klass.enable_db_query_log = int(mainconf.enable_db_query_log)
            klass.db_query_logformat = mainconf.db_query_logformat
            klass.db_query_logfile = mainconf.db_query_logfile
            klass.db_query_logfile_path = os.path.join(mainconf.logdir, mainconf.db_query_logfile)
            klass.max_db_query_logfile_size = int(mainconf.max_db_query_logfile_size)
            klass.max_db_query_logfile_size_in_bytes = int(mainconf.max_db_query_logfile_size) * 1048576
            klass.max_db_query_logfile_backups = int(mainconf.max_db_query_logfile_backups)

            # Filelist Database
            klass.video_file_table_name = 'video_files'
            klass.video_queue_table_name = 'video_queue'
            klass.youtube_cpn_table_name = 'youtube_cpns'

            # Network
            klass.cache_host = str(mainconf.cache_host).strip()
            klass.proxy = mainconf.proxy.strip()
            klass.proxy_username = mainconf.proxy_username.strip()
            klass.proxy_password = mainconf.proxy_password.strip()
            klass.max_cache_speed = int(mainconf.max_cache_speed) * 1024
            klass.id = ''

            # Other
            klass.pid = os.getpid()

            klass.min_android_app_size = int(mainconf.min_android_app_size)
            klass.max_android_app_size = int(mainconf.max_android_app_size)
        except Exception, e:
            syslog_msg('Could not load options from configuration file! Debug: '  + traceback.format_exc().replace('\n', ''))
            return None

        # Website specific options
        try:
            klass.website_cache_dir = {}
            klass.enabled_websites = {}
            for website_id in klass.websites:
                klass.website_cache_dir[website_id] = eval('mainconf.' + website_id + '_cache_dir')
                klass.enabled_websites[website_id] = int(eval('mainconf.enable_' + website_id + '_cache'))
                setattr(klass, 'enable_' + website_id + '_cache', klass.enabled_websites[website_id])
            klass.enabled_website_keys = filter(lambda x: klass.enabled_websites[x], klass.enabled_websites.keys())

            klass.max_youtube_video_quality = int(mainconf.max_youtube_video_quality.strip('p'))
            klass.min_youtube_views = int(mainconf.min_youtube_views)
            klass.enable_youtube_format_support = int(mainconf.enable_youtube_format_support)
            klass.enable_youtube_html5_videos = int(mainconf.enable_youtube_html5_videos)
            klass.enable_youtube_3d_videos = int(mainconf.enable_youtube_3d_videos)
            klass.enable_youtube_partial_caching = int(mainconf.enable_youtube_partial_caching)
            if generate_crossdomain_files:
                if not klass.enable_youtube_partial_caching:
                    klass.arg_drop_list['youtube'].append('range')
                    for dir in klass.base_dir_list:
                        os.path.isfile(os.path.join(dir, 'youtube_crossdomain.xml')) and os.unlink(os.path.join(dir, 'youtube_crossdomain.xml'))
                else:
                    for dir in klass.base_dir_list:
                        generate_youtube_crossdomain(os.path.join(dir, 'youtube_crossdomain.xml'), klass.videocache_user, True)
        except Exception, e:
            syslog_msg('Could not set website specific options. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # Create a list of cache directories available
        try:
            base_dirs = {}
            for website_id in klass.websites:
                base_dirs[website_id] = [os.path.join(dir, klass.website_cache_dir[website_id]) for dir in klass.base_dir_list]
            base_dirs[klass.temp_dir] = [os.path.join(dir, klass.temp_dir) for dir in klass.base_dir_list]
            klass.base_dirs = base_dirs
        except Exception, e:
            syslog_msg('Could not build a list of cache directories. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # Set up low and high threshold for disk cleanup
        if not skip_disk_size_calculation:
            try:
                base_dir_thresholds = {}
                for cache_dir in klass.base_dir_list:
                    size = partition_size(cache_dir)
                    base_dir_thresholds[cache_dir] = { 'low' : int(size * cache_swap_low / 100.0), 'high' : int(size * cache_swap_high / 100.0) }
                klass.base_dir_thresholds = base_dir_thresholds
            except Exception, e:
                syslog_msg('Could not calculate partition size for cache directories. Debug: ' + traceback.format_exc().replace('\n', ''))
                return None

        try:
            klass.cache_alias = 'videocache'
            klass.cache_url = 'http://' + klass.cache_host + '/'
            cache_host_parts = klass.cache_host.split(':')
            if len(cache_host_parts) == 1:
                klass.cache_host_ip = cache_host_parts[0]
            elif len(cache_host_parts) == 2:
                klass.cache_host_ip = cache_host_parts[0]
            else:
                klass.cache_host_ip = None
        except Exception, e:
            syslog_msg('Could not generate Cache URL for serving videos from cache. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        try:
            klass.proxy_server = None
            klass.this_proxy_server = None
            if klass.proxy:
                if klass.proxy_username and klass.proxy_password:
                    proxy_parts = urlparse.urlsplit(klass.proxy)
                    klass.proxy_server = 'http://%s:%s@%s/' % (klass.proxy_username, klass.proxy_password, klass.proxy)
                else:
                    klass.proxy_server = 'http://%s/' % klass.proxy
            if klass.this_proxy:
                klass.this_proxy_server = 'http://%s/' % (klass.this_proxy)
        except Exception, e:
            syslog_msg('Could not set proxy for caching videos. Debug: ' + traceback.format_exc().replace('\n', ''))
            return None

        # HTTP Headers for caching videos
        klass.redirect_code = '302'
        klass.std_headers = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.79 Safari/535.11',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8',
            },
            {
                'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729)',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept': 'image/jpeg, application/x-ms-application, image/gif, application/xaml+xml, image/pjpeg, application/x-ms-xbap, */*',
                'Accept-Language': 'en-US',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; rv:11.0) Gecko/20100101 Firefox/11.0',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Chrome/16.0.912.63 Safari/535.7',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.13) Gecko/20101209 Fedora/3.6.13-1.fc13 Firefox/3.6.13 GTB7.1',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:8.0.1) Gecko/20100101 Firefox/8.0.1',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux i686; rv:2.0) Gecko/20100101 Firefox/4.0',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.19 (KHTML, like Gecko) Chrome/18.0.1025.142 Safari/535.19',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8',
            },
            {
                'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.14) Gecko/20110218 Firefox/3.6.14',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            {
                'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; InfoPath.2; .NET4.0C; .NET CLR 2.0.50727)',
                'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
                'Accept': 'image/gif, image/jpeg, image/pjpeg, image/pjpeg, application/x-shockwave-flash, application/vnd.ms-excel, application/vnd.ms-powerpoint, application/msword, application/xaml+xml, application/x-ms-xbap, application/x-ms-application, */*',
                'Accept-Language': 'en-us',
            },
        ]
        klass.num_std_headers = len(klass.std_headers)

        klass.vc_logger = None
        klass.vcs_logger = None
        klass.trace_logger = None
        klass.vcc_logger = None
        klass.db_logger = None

        klass.initialized = True
        klass.halt = False

    @classmethod
    def set_loggers(klass):
        if klass.loggers_set:
            return

        # Set loggers
        try:
            for key in klass.format_map:
                klass.logformat = klass.logformat.replace(key, klass.format_map[key])
                klass.scheduler_logformat = klass.scheduler_logformat.replace(key, klass.format_map[key])
                klass.cleaner_logformat = klass.cleaner_logformat.replace(key, klass.format_map[key])
                klass.db_query_logformat = klass.db_query_logformat.replace(key, klass.format_map[key])
            # Main Videocache Logfile
            if klass.enable_videocache_log:
                klass.vc_logger = logging.Logger('VideocacheLog')
                klass.vc_logger.setLevel(logging.DEBUG)
                vc_log_handler = MyConcurrentRotatingFileHandler(klass.logfile_path, mode = 'a', maxBytes = klass.max_logfile_size_in_bytes, backupCount = klass.max_logfile_backups)
                klass.vc_logger.addHandler(vc_log_handler)

            # Scheduler Logfile
            if klass.enable_scheduler_log:
                klass.vcs_logger = logging.Logger('VideocacheSchedulerLog')
                klass.vcs_logger.setLevel(logging.DEBUG)
                vcs_log_handler = MyConcurrentRotatingFileHandler(klass.scheduler_logfile_path, mode = 'a', maxBytes = klass.max_scheduler_logfile_size_in_bytes, backupCount = klass.max_scheduler_logfile_backups)
                klass.vcs_logger.addHandler(vcs_log_handler)

            # Trace log
            if klass.enable_trace_log:
                klass.trace_logger = logging.Logger('VideocacheTraceLog')
                klass.trace_logger.setLevel(logging.DEBUG)
                trace_log_handler = MyConcurrentRotatingFileHandler(klass.tracefile_path, mode = 'a', maxBytes = klass.max_tracefile_size_in_bytes, backupCount = klass.max_tracefile_backups)
                klass.trace_logger.addHandler(trace_log_handler)

            # Videocache Cleaner Logfile
            if klass.enable_cleaner_log:
                klass.vcc_logger = logging.Logger('VideocacheCleanerLog')
                klass.vcc_logger.setLevel(logging.DEBUG)
                vcc_log_handler = MyConcurrentRotatingFileHandler(klass.cleaner_logfile_path, mode = 'a', maxBytes = klass.max_cleaner_logfile_size_in_bytes, backupCount = klass.max_cleaner_logfile_backups)
                klass.vcc_logger.addHandler(vcc_log_handler)

            # DB Logfile
            if klass.enable_db_query_log:
                klass.db_logger = logging.Logger('DatabaseLog')
                klass.db_logger.setLevel(logging.DEBUG)
                db_log_handler = MyConcurrentRotatingFileHandler(klass.db_query_logfile_path, mode = 'a', maxBytes = klass.max_db_query_logfile_size_in_bytes, backupCount = klass.max_db_query_logfile_backups)
                klass.db_logger.addHandler(db_log_handler)

        except Exception, e:
            syslog_msg('Could not set logging! Debug: '  + traceback.format_exc().replace('\n', ''))
            klass.halt = True
        loggers_set = True

    @classmethod
    def reset(klass):
        klass.initialized = False
        klass.loggers_set = False
        klass.halt = True
        klass.initialize(klass.config_file, klass.generate_crossdomain_files, klass.skip_disk_size_calculation)

