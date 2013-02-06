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
import datetime
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

# Colored messages on terminal
def red(msg):#{{{
    return "\033[1;31m%s\033[0m" % msg

def blue(msg):
    return "\033[1;36m%s\033[0m" % msg

def green(msg):
    return "\033[1;32m%s\033[0m" % msg#}}}

def current_time():
    return int(time.time())

def datetime_to_timestamp(t):
    return int(time.mktime(t.timetuple()))

def timestamp_to_datetime(t):
    return datetime.datetime.fromtimestamp(float(t))

def is_valid_domain_port(name):
    if re.compile('^[a-z0-9]+([\-\.]{1}[a-z0-9]+)*\.[a-z]{2,6}(:[0-9]{1,5})?$').match(name):
        return True
    return False

def is_valid_ip(ip):
    try:
        if len(filter(lambda x: 0 <= int(x) <= 255, ip.split('.'))) == 4:
            return True
    except Exception, e:
        pass
    return False

def is_valid_host_port(host_port, port_optional = False):
    if is_valid_domain_port(host_port): return True

    if ':' in host_port:
        ip, port = host_port.split(':')
        if not port.isdigit():
            return False
        port = int(port)
        if port < 0 or port > 65535:
            return False
    elif not port_optional:
        return False
    return is_valid_ip(host_port.split(':')[0])

def is_valid_email(email):
    if re.compile('^[^@\ ]+@([A-Za-z0-9]+.){1,3}[A-Za-z]{2,6}$').match(email):
        return True
    return False

def is_valid_user(user):
    try:
        pwd.getpwnam(user)
        return True
    except:
        return False

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

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

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
    print >>sys.stderr, message
    sys.exit(1)

def log_traceback():
    print blue('\n' + '-' * 25 + 'Traceback Begin' + '-' * 25)
    print traceback.format_exc(),
    print blue('-' * 25 + 'Traceback End' + '-' * 27 + '\n')

def generate_youtube_crossdomain(xdomain_file, user, quiet = False):
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
        set_permissions_and_ownership(xdomain_file, user)
        if not quiet: print "Generated youtube crossdomain file : " + xdomain_file
    except:
        if not quiet: print "Failed to generate youtube crossdomain file : " + xdomain_file
        log_traceback()
        return False
    return True

def generate_httpd_conf(conf_file, base_dir_list, cache_host, hide_cache_dirs = False, quiet = False):
    """Generates /etc/httpd/conf.d/videocache.conf for apache web server for serving videos."""
    cache_host_ip = cache_host.split(':')[0]
    if hide_cache_dirs:
        hide = "-Indexes"
    else:
        hide = "+Indexes"

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
<Directory %s>
  Options %s
  Order Allow,Deny
  Allow from all
  <IfModule mod_headers.c>
    Header add Videocache "2.0.0"
    Header add X-Cache "HIT from %s"
  </IfModule>
  <IfModule mod_mime.c>
    AddType video/webm .webm
    AddType application/vnd.android.package-archive .android
  </IfModule>
</Directory>\n""" % (dir, hide, cache_host_ip)

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

