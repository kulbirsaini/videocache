#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from iniparse import INIConfig
from iniparse.config import Undefined

class VideocacheConfig:
    def __init__(self, config_file = '/etc/videocache.conf'):
        self.config_file = config_file

    def read(self):
        config = INIConfig(open(self.config_file))
        vcconf = VideocacheConf()

        # Pick up options' values from videocache.conf or set default if they are
        # not defined in videocache.conf .
        for option in vcconf.iterkeys():
            if isinstance(getattr(config.main, option, None), Undefined):
                setattr(config.main, option, getattr(vcconf, option).default_value)
        return config.main

class Option:
    def __init__(self, default_value = None):
        self.default_value = default_value

class VideocacheConf:
    # Options not in config file
    queue_dump_file = Option('videocache.queue')
    # Global Options
    # General
    client_email = Option('')
    enable_videocache = Option(1)
    videocache_user = Option('squid')
    max_cache_processes = Option(4)
    hit_threshold = Option(1)
    max_video_size = Option(0)
    min_video_size = Option(0)
    force_video_size = Option(1)
    cache_period = Option('')
    this_proxy = Option('')
    enable_access_log_monitoring = Option(1)
    squid_access_log = Option('')
    squid_access_log_format_combined = Option(0)
    db_hostname = Option('localhost')
    db_username = Option('videocache')
    db_password = Option('')
    db_database = Option('videocache')
    redis_hostname = Option('localhost')
    redis_port = Option(6379)
    redis_socket = Option('')
    video_queue_lifetime = Option(3600 * 24)
    active_queue_lifetime = Option(3600)
    tmp_file_lifetime = Option(3600)
    hit_time_threshold = Option(30)
    log_hit_threshold = Option(300)
    max_queue_size_per_plugin = Option(1024)
    max_log_hit_monitor_queue_size = Option(65536)
    access_log_read_timeout = Option(120)
    socket_read_block_size = Option(65536)
    trial = Option(0)

    # Apache
    skip_apache_conf = Option(0)
    apache_conf_dir = Option('')
    hide_cache_dirs = Option(1)

    # Filesystem
    base_dir = Option('/var/spool/videocache/')
    temp_dir = Option('tmp')
    base_dir_selection = Option(2)
    cache_swap_low = Option(92)
    cache_swap_high = Option(97)
    filelist_rebuild_interval = Option(86400)

    # Logging
    logdir = Option('/var/log/videocache/')
    timeformat = Option('%d/%b/%Y:%H:%M:%S')
    pidfile = Option('videocache.pid')
    # Main Logfile
    enable_videocache_log = Option(1)
    logformat = Option('%tl %p %s %i %w %c %v %m %d')
    logfile = Option('videocache.log')
    max_logfile_size = Option(50)
    max_logfile_backups = Option(4)
    # Scheduler Logfile
    enable_scheduler_log = Option(1)
    scheduler_logformat = Option('%tl %p %s %i %w %c %v %m %d')
    scheduler_logfile = Option('scheduler.log')
    max_scheduler_logfile_size = Option(50)
    max_scheduler_logfile_backups = Option(1)
    # Videocache Cleaner Logfile
    enable_cleaner_log = Option(1)
    cleaner_logformat = Option('%tl %p %s %w %c %v %m %d')
    cleaner_logfile = Option('cleaner.log')
    max_cleaner_logfile_size = Option(5)
    max_cleaner_logfile_backups = Option(1)
    # Trace file
    enable_trace_log = Option(1)
    tracefile = Option('trace.log')
    max_tracefile_size = Option(5)
    max_tracefile_backups = Option(1)
    # DB logfile
    enable_db_query_log = Option(0)
    db_query_logformat = Option('%tl %m')
    db_query_logfile = Option('database.log')
    max_db_query_logfile_size = Option(5)
    max_db_query_logfile_backups = Option(1)

    # Network
    cache_host = Option('')
    proxy = Option('')
    proxy_username = Option('')
    proxy_password = Option('')
    max_cache_speed = Option(0)

    # Android apps
    enable_android_cache = Option(1)
    android_cache_dir = Option('android')
    min_android_app_size = Option(1024)
    max_android_app_size = Option(0)

    # Youtube.com & Google.com Specific Options
    enable_youtube_cache = Option(1)
    enable_youtube_format_support = Option(3)
    enable_youtube_html5_videos = Option(1)
    enable_youtube_3d_videos = Option(1)
    max_youtube_video_quality = Option('720')
    min_youtube_views = Option(100)
    youtube_cache_dir = Option('youtube')

    # AOL.com Specific Options
    enable_aol_cache = Option(1)
    aol_cache_dir = Option('aol')

    # Bing.com Specific Options
    enable_bing_cache = Option(1)
    bing_cache_dir = Option('bing')

    # Blip.tv Specific Options
    enable_bliptv_cache = Option(1)
    bliptv_cache_dir = Option('bliptv')

    # Break.tv Specific Options
    enable_breakcom_cache = Option(1)
    breakcom_cache_dir = Option('break')

    # Dailymotion.com Specific Options
    enable_dailymotion_cache = Option(1)
    dailymotion_cache_dir = Option('dailymotion')

    # Facebook.com Specific Options
    enable_facebook_cache = Option(1)
    facebook_cache_dir = Option('facebook')

    # www.imdb.com
    enable_imdb_cache = Option(1)
    imdb_cache_dir = Option('imdb')

    # Metacafe.com Specific Options
    enable_metacafe_cache = Option(1)
    metacafe_cache_dir = Option('metacafe')

    # MySpace.com Specific Options
    enable_myspace_cache = Option(1)
    myspace_cache_dir = Option('myspace')

    # Rutube.ru Specific Options
    enable_rutube_cache = Option(1)
    rutube_cache_dir = Option('rutube')

    # Veoh.com
    enable_veoh_cache = Option(1)
    veoh_cache_dir = Option('veoh')

    # videobash.com
    enable_videobash_cache = Option(1)
    videobash_cache_dir = Option('videobash')

    # Vimeo.com Specific Options
    enable_vimeo_cache = Option(1)
    vimeo_cache_dir = Option('vimeo')

    # VK.com Specific Options
    enable_vkcom_cache = Option(1)
    vkcom_cache_dir = Option('vkcom')

    # Vube.com Specific Options
    enable_vube_cache = Option(1)
    vube_cache_dir = Option('vube')

    # Weather.com Specific Options
    enable_weather_cache = Option(1)
    weather_cache_dir = Option('weather')

    # Wrzuta.pl Specific Options
    enable_wrzuta_cache = Option(1)
    wrzuta_cache_dir = Option('wrzuta')

    # Youku.com Specific Options
    enable_youku_cache = Option(1)
    youku_cache_dir = Option('youku')

    # Pr0n sites
    # Extremetube.com Specific Options
    enable_extremetube_cache = Option(1)
    extremetube_cache_dir = Option('extremetube')

    # Hardsextube.com Specific Options
    enable_hardsextube_cache = Option(1)
    hardsextube_cache_dir = Option('hardsextube')

    # Keezmovies.com Specific Options
    enable_keezmovies_cache = Option(1)
    keezmovies_cache_dir = Option('keezmovies')

    # Pornhub.com Specific Options
    enable_pornhub_cache = Option(1)
    pornhub_cache_dir = Option('pornhub')

    # Redtube.com Specific Options
    enable_redtube_cache = Option(1)
    redtube_cache_dir = Option('redtube')

    # Slutload.com Specific Options
    enable_slutload_cache = Option(1)
    slutload_cache_dir = Option('slutload')

    # Spankwire.com Specific Options
    enable_spankwire_cache = Option(1)
    spankwire_cache_dir = Option('spankwire')

    # Tube8.com Specific Options
    enable_tube8_cache = Option(1)
    tube8_cache_dir = Option('tube8')

    # Xhamster.com Specific Options
    enable_xhamster_cache = Option(1)
    xhamster_cache_dir = Option('xhamster')

    # Xtube.com Specific Options
    enable_xtube_cache = Option(1)
    xtube_cache_dir = Option('xtube')

    # Xvideos.com Specific Options
    enable_xvideos_cache = Option(1)
    xvideos_cache_dir = Option('xvideos')

    # Youporn.com Specific Options
    enable_youporn_cache = Option(1)
    youporn_cache_dir = Option('youporn')

    info_server = Option('http://hascache.com/servers')
    video_server = Option('http://hascache.com/videoid')

    def __init__(self):
        pass

    def optionobj(self, name):
        obj = getattr(self, name, None)
        if isinstance(obj, Option):
            return obj
        else:
            raise KeyError

    def isoption(self, name):
        try:
            self.optionobj(name)
            return True
        except KeyError:
            return False

    def iterkeys(self):
        for name, item in self.iteritems():
            yield name

    def iteritems(self):
        for name in dir(self):
            if self.isoption(name):
                yield (name, getattr(self, name))

