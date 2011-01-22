#!/usr/bin/env python
#
# (C) Copyright 2008-2011 Kulbir Saini <saini@saini.co.in>
#
# For more information check http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os
import syslog
import time
import urllib
import urlparse

def syslog_msg(msg):
    syslog.syslog(syslog.LOG_ERR | syslog.LOG_DAEMON, msg)

def refine_url(url, arg_drop_list = []):
    """Returns a refined url with all the arguments mentioned in arg_drop_list dropped."""
    query = urlparse.urlsplit(url)[3]
    args = urlparse.parse_qs(query, True)
    [args.has_key(arg) and args.pop(arg) for arg in arg_drop_list]
    new_args = []
    for (k,v) in args.items():
        if len(v) > 0 and v[0] != '':
            new_args.append(k + '=' + str(v[0]))
        else:
            new_args.append(k)
    new_query = '&'.join(new_args)
    #new_query = '&'.join([k + '=' + str(v[0]) for (k,v) in args.items()])
    return (urllib.splitquery(url)[0] + '?' + new_query.rstrip('&')).rstrip('?')

def build_message(params):
    cur_time = time.time()
    local_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.localtime())
    gmt_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.gmtime())
    return params.get('logformat', '') % { 'timestamp' : int(cur_time), 'timestamp_ms' : round(cur_time, 3), 'localtime' : local_time, 'gmt_time' : gmt_time, 'process_id' : params.get('process_id', '-'), 'levelname' : params.get('levelname', '-'), 'client_ip' : params.get('client_ip', '-'), 'website_id' : params.get('website_id', '-').upper(), 'code' : params.get('code', '-'), 'video_id' : params.get('video_id', '-'), 'message' : params.get('message', '-'), 'debug' : params.get('debug', '-') }

def build_trace(params):
    local_time = time.strftime(params.get('timeformat', '%d/%b/%Y:%H:%M:%S'), time.localtime())
    return params.get('trace_logformat', '') % { 'localtime' : local_time, 'process_id' : params.get('process_id', '-'), 'client_ip' : params.get('client_ip', '-'), 'website_id' : params.get('website_id', '-').upper(), 'code' : params.get('code', '-'), 'video_id' : params.get('video_id', '-'), 'message' : params.get('message', '-') }

def get_youtube_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    dict = urlparse.parse_qs(query)
    if dict.has_key('video_id'):
        video_id = dict['video_id'][0]
    elif dict.has_key('docid'):
        video_id = dict['docid'][0]
    elif dict.has_key('id'):
        video_id = dict['id'][0]
    else:
        video_id = None
    return video_id

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    dict = urlparse.parse_qs(query)
    if dict.has_key('fmt'):
        format_id = dict['fmt'][0]
    elif dict.has_key('itag'):
        format_id = dict['itag'][0]
    else:
        format_id = 34
    return format_id

def proc_test(pid):
    try:
        return os.path.exists("/proc/" + str(pid))
    except Exception, e:
        return None

def is_running(pid):
    import sys
    import os
    import errno

    try:
        os.kill(int(pid), 0)
    except OSError, e:
        if e.errno == errno.ESRCH:
            return False
        elif e.errno == errno.EPERM:
            return None
        else:
            return None
    except Exception, e:
        return None
    else:
        return True

