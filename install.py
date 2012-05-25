#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

try:
    from optparse import OptionParser
    import os
    import pwd
    import sys
    import traceback
    import urllib2
except ImportError, e:
    print 'Error:', e.args[0]
    print 'One of the critical modules is missing. Please make sure that you are using Python 2.4.3 or later.'

def check_module(module_info):
    try:
        exec('import %s' % module_info['name'])
    except Exception, e:
        return False
    return True

def install_module(module_info):
    file = open(os.path.join(tmp_dir, '%s.tar.gz' % module_info['name']), 'w')
    file.write(urllib2.urlopen(module_info['url']).read())
    file.close()
    pass

def check_and_install_dependencies():
    for module_info in python_modules:
        if not check_module(module_info):
            if not install_module(module_info):
                break

if __name__ == '__main__':

    python_modules = [
        {  'name'  :  'setuptools',  'url'  :  'https://github.com/kulbirsaini/videocache-dependencies/blob/master/setuptools.tar.gz?raw=true'  },
        {  'name'  :  'netifaces',   'url'  :  'https://github.com/kulbirsaini/videocache-dependencies/blob/master/netifaces.tar.gz?raw=true'   },
        {  'name'  :  'ctypes',      'url'  :  'https://github.com/kulbirsaini/videocache-dependencies/blob/master/ctypes.tar.gz?raw=true'      },
        {  'name'  :  'iniparse',    'url'  :  'https://github.com/kulbirsaini/videocache-dependencies/blob/master/iniparse.tar.gz?raw=true'    }
    ]
    tmp_dir = '/tmp'

