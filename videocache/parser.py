#!/usr/bin/python -tt

import re
import urlparse
import urlgrabber
import os.path

_KEYCRE = re.compile(r"\$(\w+)")

class BaseError(Exception):
    def __init__(self, value=None):
        Exception.__init__(self)
        self.value = value
    def __str__(self):
        return "%s" %(self.value,)

class ConfigError(BaseError):
    pass

def varReplace(raw, vars):
    done = []

    while raw:
        m = _KEYCRE.search(raw)
        if not m:
            done.append(raw)
            break
        varname = m.group(1).lower()
        replacement = vars.get(varname, m.group())

        start, end = m.span()
        done.append(raw[:start])
        done.append(replacement)
        raw = raw[end:]

    return ''.join(done)

class ConfigPreProcessor:
    
    def __init__(self, configfile, vars=None):
        self._vars = vars
        
        self.mode = 'r' 
        
        scheme = urlparse.urlparse(configfile)[0]
        if scheme == '':
            if configfile[0] != '/':
                configfile = os.getcwd() + '/' + configfile
            url = 'file://' + configfile
        else:
            url = configfile
        
        self._incstack = []
        self._alreadyincluded = []
        
        fo = self._pushfile( url )
        if fo is None: 
            raise ConfigError, 'Error accessing file: %s' % url
        
    def readline( self, size=0 ):
        line=''
        while len(self._incstack) > 0:
            fo = self._incstack[-1]
            line = fo.readline()
            if len(line) > 0:
                m = re.match( r'\s*include\s*=\s*(?P<url>.*)', line )
                if m:
                    url = m.group('url')
                    if len(url) == 0:
                        raise ConfigError, \
                             'Error parsing config %s: include must specify file to include.' % (self.name)
                    else:
                        fo = self._pushfile( url )
                else:
                    break
            else:
                self._popfile()
        
        if self._vars:
            return varReplace(line, self._vars)
        return line
    
    
    def _absurl( self, url ):
        if len(self._incstack) == 0:
            return url
        else:
            return urlparse.urljoin( self.geturl(), url )
    
    
    def _pushfile( self, url ):
        absurl = self._absurl(url)
        if self._urlalreadyincluded(absurl):
            return None
        try:
            fo = urlgrabber.grabber.urlopen(absurl)
        except urlgrabber.grabber.URLGrabError, e:
            fo = None
        if fo is not None:
            self.name = absurl
            self._incstack.append( fo )
            self._alreadyincluded.append(absurl)
        else:
            raise ConfigError, \
                  'Error accessing file for config %s' % (absurl)

        return fo
    
    
    def _popfile( self ):
        fo = self._incstack.pop()
        fo.close()
        if len(self._incstack) > 0:
            self.name = self._incstack[-1].geturl()
        else:
            self.name = None
    
    
    def _urlalreadyincluded( self, url ):
        for eurl in self._alreadyincluded:
            if eurl == url: return 1
        return 0
    
    
    def geturl(self): return self.name
