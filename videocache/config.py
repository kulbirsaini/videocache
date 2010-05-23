#!/usr/bin/python -t

import os
import warnings
import copy
import urlparse
from parser import ConfigPreProcessor
from iniparse.compat import NoSectionError, NoOptionError, ConfigParser
from iniparse.compat import ParsingError

class BaseError(Exception):
    def __init__(self, value=None):
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        return "%s" %(self.value,)

class ConfigError(BaseError):
    pass

class Option(object):
    def __init__(self, default=None):
        self._setattrname()
        self.inherit = False
        self.default = default

    def _setattrname(self):
        self._attrname = '__opt%d' % id(self)

    def __get__(self, obj, objtype):
        if obj is None:
            return self

        return getattr(obj, self._attrname, None)

    def __set__(self, obj, value):
        if isinstance(value, basestring):
            try:
                value = self.parse(value)
            except ValueError, e:
                raise ValueError('Error parsing %r: %s' % (value, str(e)))

        setattr(obj, self._attrname, value)

    def setup(self, obj, name):
        setattr(obj, self._attrname, copy.copy(self.default))

    def clone(self):
        new = copy.copy(self)
        new._setattrname()
        return new

    def parse(self, s):
        return s

    def tostring(self, value):
        return str(value)

def Inherit(option_obj):
    new_option = option_obj.clone()
    new_option.inherit = True
    return new_option

class ListOption(Option):
    def __init__(self, default=None):
        if default is None:
            default = []
        super(ListOption, self).__init__(default)

    def parse(self, s):
        s = s.replace('\n', ' ')
        s = s.replace(',', ' ')
        return s.split()

    def tostring(self, value):
        return '\n '.join(value)

class UrlOption(Option):
    def __init__(self, default=None, schemes=('http', 'ftp', 'file', 'https'), 
            allow_none=False):
        super(UrlOption, self).__init__(default)
        self.schemes = schemes
        self.allow_none = allow_none

    def parse(self, url):
        url = url.strip()

        if url.lower() == '_none_':
            if self.allow_none:
                return None
            else:
                raise ValueError('"_none_" is not a valid value')

        (s,b,p,q,f,o) = urlparse.urlparse(url)
        if s not in self.schemes:
            raise ValueError('URL must be %s not "%s"' % (self._schemelist(), s))

        return url

    def _schemelist(self):
        if len(self.schemes) < 1:
            return 'empty'
        elif len(self.schemes) == 1:
            return self.schemes[0]
        else:
            return '%s or %s' % (', '.join(self.schemes[:-1]), self.schemes[-1])

class UrlListOption(ListOption):
    def __init__(self, default=None, schemes=('http', 'ftp', 'file', 'https')):
        super(UrlListOption, self).__init__(default)

        self._urloption = UrlOption(schemes=schemes)
        
    def parse(self, s):
        out = []
        for url in super(UrlListOption, self).parse(s):
            out.append(self._urloption.parse(url))
        return out


class IntOption(Option):
    def __init__(self, default=None, range_min=None, range_max=None):
        super(IntOption, self).__init__(default)
        self._range_min = range_min
        self._range_max = range_max
        
    def parse(self, s):
        try:
            val = int(s)
        except (ValueError, TypeError), e:
            raise ValueError('invalid integer value')
        if self._range_max is not None and val > self._range_max:
            raise ValueError('out of range integer value')
        if self._range_min is not None and val < self._range_min:
            raise ValueError('out of range integer value')
        return val

class PositiveIntOption(IntOption):
    def __init__(self, default=None, range_min=0, range_max=None,
                 names_of_0=None):
        super(PositiveIntOption, self).__init__(default, range_min, range_max)
        self._names0 = names_of_0

    def parse(self, s):
        if s in self._names0:
            return 0
        return super(PositiveIntOption, self).parse(s)

class SecondsOption(Option):
    MULTS = {'d': 60 * 60 * 24, 'h' : 60 * 60, 'm' : 60, 's': 1}

    def parse(self, s):
        if len(s) < 1:
            raise ValueError("no value specified")

        if s == "-1" or s == "never":
            return -1
        if s[-1].isalpha():
            n = s[:-1]
            unit = s[-1].lower()
            mult = self.MULTS.get(unit, None)
            if not mult:
                raise ValueError("unknown unit '%s'" % unit)
        else:
            n = s
            mult = 1

        try:
            n = float(n)
        except (ValueError, TypeError), e:
            raise ValueError('invalid value')

        if n < 0:
            raise ValueError("seconds value may not be negative")

        return int(n * mult)

class BoolOption(Option):
    def parse(self, s):
        s = s.lower()
        if s in ('0', 'no', 'false'):
            return False
        elif s in ('1', 'yes', 'true'):
            return True
        else:
            raise ValueError('invalid boolean value')

    def tostring(self, value):
        if value:
            return "1"
        else:
            return "0"

class FloatOption(Option):
    def parse(self, s):
        try:
            return float(s.strip())
        except (ValueError, TypeError):
            raise ValueError('invalid float value')

class SelectionOption(Option):
    def __init__(self, default=None, allowed=()):
        super(SelectionOption, self).__init__(default)
        self._allowed = allowed
        
    def parse(self, s):
        if s not in self._allowed:
            raise ValueError('"%s" is not an allowed value' % s)
        return s

class BytesOption(Option):
    MULTS = {
        'k': 1024,
        'm': 1024*1024,
        'g': 1024*1024*1024,
    }

    def parse(self, s):
        if len(s) < 1:
            raise ValueError("no value specified")

        if s[-1].isalpha():
            n = s[:-1]
            unit = s[-1].lower()
            mult = self.MULTS.get(unit, None)
            if not mult:
                raise ValueError("unknown unit '%s'" % unit)
        else:
            n = s
            mult = 1
             
        try:
            n = float(n)
        except ValueError:
            raise ValueError("couldn't convert '%s' to number" % n)

        if n < 0:
            raise ValueError("bytes value may not be negative")

        return int(n * mult)

class ThrottleOption(BytesOption):
    def parse(self, s):
        if len(s) < 1:
            raise ValueError("no value specified")

        if s[-1] == '%':
            n = s[:-1]
            try:
                n = float(n)
            except ValueError:
                raise ValueError("couldn't convert '%s' to number" % n)
            if n < 0 or n > 100:
                raise ValueError("percentage is out of range")
            return n / 100.0
        else:
            return BytesOption.parse(self, s)


class BaseConfig(object):
    def __init__(self):
        self._section = None

        for name in self.iterkeys():
            option = self.optionobj(name)
            option.setup(self, name)

    def __str__(self):
        out = []
        out.append('[%s]' % self._section)
        for name, value in self.iteritems():
            out.append('%s: %r' % (name, value))
        return '\n'.join(out)

    def populate(self, parser, section, parent=None):
        self.cfg = parser
        self._section = section

        for name in self.iterkeys():
            option = self.optionobj(name)
            value = None
            try:
                value = parser.get(section, name)
            except (NoSectionError, NoOptionError):
                if parent and option.inherit:
                    value = getattr(parent, name)
               
            if value is not None:
                setattr(self, name, value)

    def optionobj(cls, name):
        obj = getattr(cls, name, None)
        if isinstance(obj, Option):
            return obj
        else:
            raise KeyError
    optionobj = classmethod(optionobj)

    def isoption(cls, name):
        try:
            cls.optionobj(name)
            return True
        except KeyError:
            return False
    isoption = classmethod(isoption)

    def iterkeys(self):
        for name, item in self.iteritems():
            yield name

    def iteritems(self):
        for name in dir(self):
            if self.isoption(name):
                yield (name, getattr(self, name))

    def write(self, fileobj, section=None, always=()):
        if section is None:
            if self._section is None:
                raise ValueError("not populated, don't know section")
            section = self._section

        cfgOptions = self.cfg.options(section)
        for name,value in self.iteritems():
            option = self.optionobj(name)
            if always is None or name in always or option.default != value or name in cfgOptions :
                self.cfg.set(section,name, option.tostring(value))
        self.cfg.write(fileobj)

    def getConfigOption(self, option, default=None):
        if hasattr(self, option):
            return getattr(self, option)
        return default

    def setConfigOption(self, option, value):
        if hasattr(self, option):
            setattr(self, option, value)
        else:
            raise ConfigError, 'No such option %s' % option

class StartupConf(BaseConfig):
    debuglevel = IntOption(2, 0, 10)
    errorlevel = IntOption(2, 0, 10)

    installroot = Option('/')
    config_file_path = Option('/etc/videocache.conf')

class TestConf(StartupConf):
    # Global Options
    enable_video_cache = Option(1)
    base_dir = Option('/var/spool/videocache/')
    temp_dir = Option('tmp')
    disk_avail_threshold = Option(100)
    enable_videocache_cleaner = Option(0)
    video_lifetime = Option(60)
    max_parallel_downloads = Option(30)
    cache_host = Option('127.0.0.1')
    hit_threshold = Option(2)
    rpc_host = Option('127.0.0.1')
    rpc_port = Option(9100)
    logdir = Option('/var/log/videocache/')
    max_logfile_size = Option(10)
    max_logfile_backups = Option(10)
    proxy = Option()
    proxy_username = Option()
    proxy_password = Option()

    # Youtube.com Specific Options
    enable_youtube_cache = Option(1)
    youtube_cache_dir = Option('youtube')
    max_youtube_video_size = Option(0)
    min_youtube_video_size = Option(0)

    # Metacafe.com Specific Options
    enable_metacafe_cache = Option(1)
    metacafe_cache_dir = Option('metacafe')
    max_metacafe_video_size = Option(0)
    min_metacafe_video_size = Option(0)

    # Dailymotion.com Specific Options
    enable_dailymotion_cache = Option(1)
    dailymotion_cache_dir = Option('dailymotion')
    max_dailymotion_video_size = Option(0)
    min_dailymotion_video_size = Option(0)

    # Google.com Specific Options
    enable_google_cache = Option(1)
    google_cache_dir = Option('google')
    max_google_video_size = Option(0)
    min_google_video_size = Option(0)

    # Redtube.com Specific Options
    enable_redtube_cache = Option(1)
    redtube_cache_dir = Option('redtube')
    max_redtube_video_size = Option(0)
    min_redtube_video_size = Option(0)

    # Xtube.com Specific Options
    enable_xtube_cache = Option(1)
    xtube_cache_dir = Option('xtube')
    max_xtube_video_size = Option(0)
    min_xtube_video_size = Option(0)

    # Vimeo.com Specific Options
    enable_vimeo_cache = Option(1)
    vimeo_cache_dir = Option('vimeo')
    max_vimeo_video_size = Option(0)
    min_vimeo_video_size = Option(0)

    # Wrzuta.pl Specific Options
    enable_wrzuta_cache = Option(1)
    wrzuta_cache_dir = Option('wrzuta')
    max_wrzuta_video_size = Option(0)
    min_wrzuta_video_size = Option(0)

    # Youporn.com Specific Options
    enable_youporn_cache = Option(1)
    youporn_cache_dir = Option('youporn')
    max_youporn_video_size = Option(0)
    min_youporn_video_size = Option(0)

    # Soapbox.msn.com Specific Options
    enable_soapbox_cache = Option(1)
    soapbox_cache_dir = Option('soapbox')
    max_soapbox_video_size = Option(0)
    min_soapbox_video_size = Option(0)

    # Tube8.com Specific Options
    enable_tube8_cache = Option(1)
    tube8_cache_dir = Option('tube8')
    max_tube8_video_size = Option(0)
    min_tube8_video_size = Option(0)

    # Tvuol.uol.com.br Specific Options
    enable_tvuol_cache = Option(1)
    tvuol_cache_dir = Option('tvuol')
    max_tvuol_video_size = Option(0)
    min_tvuol_video_size = Option(0)

    # Blip.tv Specific Options
    enable_bliptv_cache = Option(1)
    bliptv_cache_dir = Option('bliptv')
    max_bliptv_video_size = Option(0)
    min_bliptv_video_size = Option(0)

    # Break.tv Specific Options
    enable_break_cache = Option(1)
    break_cache_dir = Option('break')
    max_break_video_size = Option(0)
    min_break_video_size = Option(0)

    _reposlist = []

def readStartupConfig(configfile, root):

    StartupConf.installroot.default = root
    startupconf = StartupConf()
    startupconf.config_file_path = configfile
    parser = ConfigParser()
    confpp_obj = ConfigPreProcessor(configfile)
    try:
        parser.readfp(confpp_obj)
    except ParsingError, e:
        raise ConfigError("Parsing file failed: %s" % e)
    startupconf.populate(parser, 'main')

    startupconf._parser = parser

    return startupconf

def readMainConfig(startupconf):
    testconf = TestConf()
    testconf.populate(startupconf._parser, 'main')

    testconf.config_file_path = startupconf.config_file_path
    if os.path.exists(startupconf.config_file_path):
        testconf.config_file_age = os.stat(startupconf.config_file_path)[8]
    else:
        testconf.config_file_age = 0
    
    testconf.debuglevel = startupconf.debuglevel
    testconf.errorlevel = startupconf.errorlevel
    
    return testconf

def getOption(conf, section, name, option):
    try: 
        val = conf.get(section, name)
    except (NoSectionError, NoOptionError):
        return option.default
    return option.parse(val)

