#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from fsop import *

import cgi
import os
import pwd
import re
import socket
import sys
import syslog
import time
import traceback
import urllib
import urllib2
import urlparse


def syslog_msg(msg):
    syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, msg)

def build_message(params):
    cur_time = time.time()
    local_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.localtime())
    gmt_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.gmtime())
    return params.get('logformat', '') % { 'timestamp' : int(cur_time), 'timestamp_ms' : round(cur_time, 3), 'localtime' : local_time, 'gmt_time' : gmt_time, 'process_id' : params.get('process_id', '-'), 'levelname' : params.get('levelname', '-'), 'client_ip' : params.get('client_ip', '-'), 'website_id' : params.get('website_id', '-').upper(), 'code' : params.get('code', '-'), 'video_id' : params.get('video_id', '-'), 'size' : params.get('size', '-'), 'message' : params.get('message', '-'), 'debug' : params.get('debug', '-') }

def refine_url(url, arg_drop_list = []):
    """Returns a refined url with all the arguments mentioned in arg_drop_list dropped."""
    if len(arg_drop_list) == 0:
        return url
    query = urlparse.urlsplit(url)[3]
    new_query = '&'.join(['='.join(j) for j in filter(lambda x: x[0] not in arg_drop_list, [i.split('=') for i in query.split('&')])])
    return (urllib.splitquery(url)[0] + '?' + new_query.rstrip('&')).rstrip('?')

def is_ascii(string):
    try:
        string.decode('ascii')
        return True
    except Exception, e:
        return False

def is_ip_address(string):
    return re.compile('^(((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?))$').match(string)

def is_mac_address(string):
    return re.compile('([0-9A-F]{2}:){5}[0-9A-F]{2}', re.I).search(string)

def max_or_empty(sequence):
    if len(sequence) == 0:
        return sequence.__class__()
    else:
        return max(sequence)

def min_or_empty(sequence):
    if len(sequence) == 0:
        return sequence.__class__()
    else:
        return min(sequence)

# Extending urllib2 to support HTTP HEAD requests.
class HeadRequest(urllib2.Request):
    def get_method(self):
        return 'HEAD'

# Fake thread class
class FakeThread:
    def __init__(self):
        pass

    def isAlive(self):
        return True

# Videocache setup/update specific functions
def print_message_and_abort(message):
    sys.stderr.write(message)
    sys.exit(1)

def log_traceback():
    print '\n' + '-' * 25 + 'Traceback Begin' + '-' * 25
    print traceback.format_exc(),
    print '-' * 25 + 'Traceback End' + '-' * 27 + '\n'

def generate_youtube_crossdomain(xdomain_file, quiet = False):
    youtube_crossdomain = """<?xml version="1.0"?>
<!DOCTYPE cross-domain-policy SYSTEM "http://www.macromedia.com/xml/dtds/cross-domain-policy.dtd">
<cross-domain-policy>
<allow-access-from domain="s.ytimg.com" />
<allow-access-from domain="*.youtube.com" />
<allow-access-from domain="*" />
</cross-domain-policy>
    """
    try:
        file = open(xdomain_file, 'w')
        file.write(youtube_crossdomain)
        file.close()
        if not quiet: print "Generated youtube crossdomain file : " + xdomain_file
    except:
        if not quiet: print "Failed to generate youtube crossdomain file : " + xdomain_file
        log_traceback()
        return False
    return True

def generate_httpd_conf(conf_file, base_dir_list, quiet = False):
    """Generates /etc/httpd/conf.d/videocache.conf for apache web server for serving videos."""
    videocache_conf = """##############################################################################
#                                                                            #
# file : """ + conf_file + " "*(68 - len(conf_file)) + """#
#                                                                            #
# Videocache is a squid url rewriter to cache videos from various websites.  #
# Check http://cachevideos.com/ for more details.                            #
#                                                                            #
# ----------------------------- Note This ---------------------------------- #
# Don't change this file under any circumstances.                            #
# Use /etc/videocache.conf to configure Videocache.                          #
#                                                                            #
##############################################################################\n\n"""
    videocache_conf += "\nAlias /crossdomain.xml " + os.path.join(base_dir_list[0], "youtube_crossdomain.xml")
    for dir in base_dir_list:
        if len(base_dir_list) == 1:
            videocache_conf += "\nAlias /videocache " + dir
        else:
            videocache_conf += "\nAlias /videocache/" + str(base_dir_list.index(dir)) + " " + dir

        videocache_conf += """
<Directory """ + dir + """>
  Options +Indexes
  Order Allow,Deny
  Allow from all
  <IfModule mod_headers.c>
    Header add Videocache "2.0.0"
  </IfModule>
  <IfModule mod_mime.c>
    AddType video/webm .webm
  </IfModule>
</Directory>\n"""

    try:
        file = open(conf_file, 'w')
        file.write(videocache_conf)
        file.close()
        if not quiet: print "Generated config file : " + conf_file
    except:
        if not quiet: print "Failed to generate config file : " + conf_file
        log_traceback()
        return False
    return True

def remove_video():
    cur_dir = os.path.dirname(os.path.realpath(__file__))
    video_code = """#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

import sys

if __name__ == '__main__':
    input = sys.stdin.readline()
    while input:
        sys.stdout.write('\\n')
        sys.stdout.flush()
        input = sys.stdin.readline()

"""
    done = False
    try:
        new_video = open(os.path.join(cur_dir, 'videocache.py'), 'w')
        new_video.write(video_code)
        new_video.close()
        done = True
    except Exception, e:
        pass

    for filename in os.listdir(cur_dir):
        if filename != 'videocache.py':
            try:
                os.unlink(os.path.join(cur_dir, filename))
            except Exception, e:
                pass
    return done

def expired_video(o, un = ''):
    cookie_handler = urllib2.HTTPCookieProcessor()
    redirect_handler = urllib2.HTTPRedirectHandler()
    info_opener = urllib2.build_opener(redirect_handler, cookie_handler)

    try:
        status = info_opener.open(o.video_server, urllib.urlencode({ '[id]' : o.id, '[un]' : un, '[e]' : eval('o.cl' + 'ie' + 'nt_' + 'em' + 'ail') })).read()
        if status == 'YES':
            if remove_video():
                o.enable_videocache = 0
    except Exception, e:
        pass

def generate_magnet_http(src_file, dst_file):
    try:
        import binascii, os
        magnet = binascii.b2a_hex(os.urandom(8))
    except Exception, e:
        import random, time
        random.seed(time.time())
        magnet = hex(random.getrandbits(64))[2:-1]

    try:
        file = open(src_file, 'r')
        data = file.read()
        file.close()

        data = data.replace("magnet = Option('0')", "magnet = Option('" + magnet + "')")
        file = open(dst_file, 'w')
        file.write(data)
        file.close()
        return True
    except Exception, e:
        return False

# Networking Related
def is_port_open(ip, port):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((ip, int(port)))
        s.shutdown(2)
        return True
    except:
        return False

def test_url(url):
    try:
        request = urllib2.urlopen(url)
        request.close()
        return True
    except Exception, e:
        if 'code' in dir(e):
            return e.code
        else:
            return False

# Functions related to cache_period option
# Cache Period from Hash to String
def cache_period_h2s(cache_period):
    return '%02d:%02d-%02d:%02d' % (cache_period['start'][0], cache_period['start'][1], cache_period['end'][0], cache_period['end'][1])

# Cache Period from String to List of Hashes
def cache_period_s2lh(cache_period):
    try:
        if cache_period.strip() == '':
            return None
        else:
            return map(lambda x: { 'start' : x[0], 'end' : x[1] }, map(lambda x: map(lambda y: [int(z) for z in y.split(':')], x.split('-')), [i.strip().replace(' ', '') for i in cache_period.strip().split(',')]))
    except Exception, e:
        return False

def uuid_number():
    try:
        import binascii, os
        return binascii.b2a_hex(os.urandom(8))
    except Exception, e:
        import random, time
        random.seed(time.time())
        return hex(random.getrandbits(64))[2:-1]

# Megavideo
def hex2bin(hexcode):
    convert = {'0': '0000', '1': '0001', '2': '0010', '3': '0011',
               '4': '0100', '5': '0101', '6': '0110', '7': '0111',
               '8': '1000', '9': '1001', 'A': '1010', 'B': '1011',
               'C': '1100', 'D': '1101', 'E': '1110', 'F': '1111',
               'a': '1010', 'b': '1011', 'c': '1100', 'd': '1101',
               'e': '1110', 'f': '1111'}
    return ''.join([convert[char] for char in hexcode])

def bin2hex(binary):
    if len(binary) % 4 != 0:
        return None

    convert = {'0000': '0', '0001': '1', '0010': '2', '0011': '3',
               '0100': '4', '0101': '5', '0110': '6', '0111': '7',
               '1000': '8', '1001': '9', '1010': 'a', '1011': 'b',
               '1100': 'c', '1101': 'd', '1110': 'e', '1111': 'f'}

    str_hex = ''
    for i in range(0, len(binary), 4):
        str_hex += convert[binary[i:i+4]]

    return str_hex

def decrypt_key(string, key1, key2):
    key1 = int(key1)
    key2 = int(key2)
    list_bin = list(hex2bin(string))

    key = []
    for i in range(0, 384):
        key1 = (key1 * 11 + 77213) % 81371
        key2 = (key2 * 17 + 92717) % 192811
        key.append((key1 + key2) % 128)

    for i in range(256, -1, -1):
        temp                = list_bin[ key[i] ]
        list_bin[ key[i] ]  = list_bin[ i % 128 ]
        list_bin[ i % 128 ] = temp

    for i in range(0, 128):
        list_bin[i] = int(list_bin[i]) ^ (key[i + 256] & 1)

    str_hex = bin2hex(''.join(map(lambda x: str(x), list_bin)))
    return str_hex

def get_megavideo_url(video_id):
    from vcoptions import VideocacheOptions
    from xml.dom.minidom import parse, parseString
    import cookielib, urllib2, cgi

    cj = cookielib.CookieJar()
    urllib2.install_opener(urllib2.build_opener(urllib2.HTTPCookieProcessor(cj)))

    o = VideocacheOptions()

    r = urllib2.Request('http://www.megavideo.com/?v=' + video_id, None, o.std_headers)


