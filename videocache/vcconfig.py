#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from iniparse import INIConfig
from iniparse.config import Undefined

import os

class VideocacheConfig:
    """
    This class reads videocache.conf configuration file and sets all the option
    so that they are available via Options class.
    """

    def __init__(self, config_file = '/etc/videocache.conf', root = '/'):
        self.config_file = config_file
        self.root = root

    def read(self):
        config = INIConfig(open(os.path.join(self.root, self.config_file)))
        vcconf = VideocacheConf()

        # Pick up options' values from videocache.conf or set default if they are
        # not defined in videocache.conf .
        for option in vcconf.iterkeys():
            if isinstance(getattr(config.main, option, None), Undefined):
                setattr(config.main, option, getattr(vcconf, option).default_value)
        return config.main

class Option:
    """
    Used to set default values for options if they are not defined or commented
    in videocache.conf configuration file.
    """

    def __init__(self, default_value = None):
        self.default_value = default_value

class VideocacheConf:
    """
    All the global options should be set in this class otherwise they
    will not be available in Options class.
    """

    # Options not in config file
    queue_dump_file = Option('videocache.queue')
    # Global Options
    # General
    enable_videocache = Option(1)
    offline_mode = Option(0)
    videocache_user = Option('squid')
    enable_videocache_cleaner = Option(1)
    video_lifetime = Option(30)
    max_cache_processes = Option(30)
    hit_threshold = Option(2)
    max_video_size = Option(0)
    min_video_size = Option(0)
    client_email = Option('')

    # Filesystem
    base_dir = Option('/var/spool/videocache/')
    temp_dir = Option('tmp')
    disk_avail_threshold = Option(100)

    # Logging
    logdir = Option('/var/log/videocache/')
    timeformat = Option('%d/%b/%Y:%H:%M:%S')
    scheduler_pidfile = Option('/var/run/videocache.pid')
    # Main Logfile
    logformat = Option('%tl %p %s %i %w %c %v %m %d')
    logfile = Option('videocache.log')
    max_logfile_size = Option(10)
    max_logfile_backups = Option(10)
    # Scheduler Logfile
    scheduler_logformat = Option('%tl %p %s %i %w %c %v %m %d')
    scheduler_logfile = Option('scheduler.log')
    max_scheduler_logfile_size = Option(10)
    max_scheduler_logfile_backups = Option(10)
    # Videocache Cleaner Logfile
    cleaner_logformat = Option('%tl %p %s %w %c %v %m %d')
    cleaner_logfile = Option('cleaner.log')
    max_cleaner_logfile_size = Option(10)
    max_cleaner_logfile_backups = Option(5)
    # Trace file
    tracefile = Option('trace.log')
    max_tracefile_size = Option(10)
    max_tracefile_backups = Option(1)

    # Network
    cache_host = Option('127.0.0.1')
    rpc_host = Option('127.0.0.1')
    rpc_port = Option(9100)
    proxy = Option()
    proxy_username = Option()
    proxy_password = Option()

    # Youtube.com & Google.com Specific Options
    enable_youtube_cache = Option(1)
    youtube_cache_dir = Option('youtube')

    # Facebook.com Specific Options
    enable_facebook_cache = Option(1)
    facebook_cache_dir = Option('facebook')

    # Metacafe.com Specific Options
    enable_metacafe_cache = Option(1)
    metacafe_cache_dir = Option('metacafe')

    # Dailymotion.com Specific Options
    enable_dailymotion_cache = Option(1)
    dailymotion_cache_dir = Option('dailymotion')

    # CNN.com Specific Options
    enable_cnn_cache = Option(1)
    cnn_cache_dir = Option('cnn')

    # AOL.com Specific Options
    enable_aol_cache = Option(1)
    aol_cache_dir = Option('aol')

    # MySpace.com Specific Options
    enable_myspace_cache = Option(1)
    myspace_cache_dir = Option('myspace')

    # Xhamster.com Specific Options
    enable_xhamster_cache = Option(1)
    xhamster_cache_dir = Option('xhamster')

    # Xvideos.com Specific Options
    enable_xvideos_cache = Option(1)
    xvideos_cache_dir = Option('xvideos')

    # Pornhub.com Specific Options
    enable_pornhub_cache = Option(1)
    pornhub_cache_dir = Option('pornhub')

    # Spankwire.com Specific Options
    enable_spankwire_cache = Option(1)
    spankwire_cache_dir = Option('spankwire')

    # Hardsextube.com Specific Options
    enable_hardsextube_cache = Option(1)
    hardsextube_cache_dir = Option('hardsextube')

    # Redtube.com Specific Options
    enable_redtube_cache = Option(1)
    redtube_cache_dir = Option('redtube')

    # Xtube.com Specific Options
    enable_xtube_cache = Option(1)
    xtube_cache_dir = Option('xtube')

    # Vimeo.com Specific Options
    enable_vimeo_cache = Option(1)
    vimeo_cache_dir = Option('vimeo')

    # Wrzuta.pl Specific Options
    enable_wrzuta_cache = Option(1)
    wrzuta_cache_dir = Option('wrzuta')

    # Youporn.com Specific Options
    enable_youporn_cache = Option(1)
    youporn_cache_dir = Option('youporn')

    # Bing.com Specific Options
    enable_bing_cache = Option(1)
    bing_cache_dir = Option('bing')

    # Tube8.com Specific Options
    enable_tube8_cache = Option(1)
    tube8_cache_dir = Option('tube8')

    # Blip.tv Specific Options
    enable_bliptv_cache = Option(1)
    bliptv_cache_dir = Option('bliptv')

    # Break.tv Specific Options
    enable_break_cache = Option(1)
    break_cache_dir = Option('break')

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

