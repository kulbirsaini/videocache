#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import cgi
import os
import re
import urlparse

VALIDATE_YOUTUBE_VIDEO_ID_REGEX = re.compile('^[a-zA-Z0-9_\-]+$')
VALIDATE_YOUTUBE_DOMAIN_REGEX = re.compile('\.(youtube|youtube-nocookie|googlevideo)\.com')
YOUTUBE_VIDEO_ID_EXTRACT_REGEX1 = re.compile('\/(v|e|embed)\/([0-9a-zA-Z_-]{11})')
YOUTUBE_VIDEO_ID_EXTRACT_REGEX2 = re.compile('\/(feeds\/api\/videos)\/([0-9a-zA-Z_-]{11})\/')
YOUTUBE_VIDEO_ID_EXTRACT_REGEX3 = re.compile('\/(id|video_id|docid|v)\/([a-zA-Z0-9_\-]+)\/')
YOUTUBE_CPN_EXTRACT_REGEX = re.compile('\/cpn\/([a-zA-Z0-9_\-]+)\/')
YOUTUBE_UPN_EXTRACT_REGEX = re.compile('\/upn\/([a-zA-Z0-9_\-]+)\/')
YOUTUBE_FORMAT_EXTRACT_REGEX = re.compile('\/(itag|fmt)\/([0-9]+)\/')
YOUTUBE_VIDEO_RANGE_EXTRACT_REGEX = re.compile('\/range\/([0-9]+)-([0-9]+)\/')
YOUTUBE_VIDEO_RANGE_EXTRACT_REGEX2 = re.compile('\/begin\/([0-9]+)\/len\/([0-9]+)\/')
YOUTUBE_DOMAINS = ['.googlevideo.com', '.youtube.com', '.youtube-nocookie.com', '.youtu.be']
YOUTUBE_DOMAINS_DENY = [ 'manifest.googlevideo.com', 'manifest.youtube.com' ]

# Functions related to Youtube video ID and video format
# video_id
def is_valid_youtube_video_id(video_id):
    if video_id and len(video_id) in [11, 16]: return True
    return False

def is_long_youtube_video_id(video_id):
    if video_id and len(video_id) > 16 and len(video_id) <= 56: return True
    return False

def get_youtube_video_id_from_query(query):
    params = cgi.parse_qs(query)
    for key in ['video_id', 'id', 'v', 'docid']:
        if key in params and VALIDATE_YOUTUBE_VIDEO_ID_REGEX.match(params[key][0]) and (is_valid_youtube_video_id(params[key][0]) or is_long_youtube_video_id(params[key][0])):
            return params[key][0]
    return None

def get_youtube_video_id_from_path(path):
    for regex in [YOUTUBE_VIDEO_ID_EXTRACT_REGEX3, YOUTUBE_VIDEO_ID_EXTRACT_REGEX1, YOUTUBE_VIDEO_ID_EXTRACT_REGEX2]:
        match = regex.search(path)
        if match and len(match.groups()) == 2 and (is_valid_youtube_video_id(match.groups()[1]) or is_long_youtube_video_id(match.groups()[1])):
            return match.groups()[1]
    return None

def get_youtube_video_id_from_query_or_path(query, path):
    video_id = get_youtube_video_id_from_query(query)
    if not video_id: video_id = get_youtube_video_id_from_path(path)
    return video_id

def get_youtube_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_id_from_query_or_path(query, path)

# cpn
def get_youtube_cpn_from_query(query):
    params, cpn = cgi.parse_qs(query), None
    if 'cpn' in params: cpn = params['cpn'][0]
    return cpn

def get_youtube_cpn_from_path(path):
    cpn = None
    match = YOUTUBE_CPN_EXTRACT_REGEX.search(path)
    if match and len(match.groups()) == 1: cpn = match.groups()[0]
    return cpn

def get_youtube_cpn_from_query_or_path(query, path):
    cpn = get_youtube_cpn_from_query(query)
    if not cpn: cpn = get_youtube_cpn_from_path(path)
    return cpn

def get_youtube_cpn(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_cpn_from_query_or_path(query, path)

# upn
def get_youtube_upn_from_query(query):
    params, upn = cgi.parse_qs(query), None
    if 'upn' in params: upn = params['upn'][0]
    return upn

def get_youtube_upn_from_path(path):
    upn = None
    match = YOUTUBE_UPN_EXTRACT_REGEX.search(path)
    if match and len(match.groups()) == 1: upn = match.groups()[0]
    return upn

def get_youtube_upn_from_query_or_path(query, path):
    upn = get_youtube_upn_from_query(query)
    if not upn: upn = get_youtube_upn_from_path(path)
    return upn

def get_youtube_upn(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_upn_from_query_or_path(query, path)

# video_format
def get_youtube_video_format_from_query(query):
    params, fmt = cgi.parse_qs(query), ''
    if 'itag' in params:
        fmt = params['itag'][0]
    elif 'fmt' in params:
        fmt = params['fmt'][0]
    elif 'layout' in params and params['layout'][0].lower() == 'mobile':
        fmt = '18'
    return fmt

def get_youtube_video_format_from_path(path):
    fmt = ''
    match = YOUTUBE_FORMAT_EXTRACT_REGEX.search(path)
    if match and len(match.groups()) == 2:
        fmt = match.groups()[1]
    return fmt

def get_youtube_video_format_from_query_or_path(query, path):
    fmt = get_youtube_video_format_from_query(query)
    if fmt == '': fmt = get_youtube_video_format_from_path(path)
    return fmt

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_format_from_query_or_path(query, path)

# video range
def get_youtube_video_range_from_query(query):
    params, start, end = cgi.parse_qs(query), 0, 0
    if 'range' in params:
        try:
            start, end = [int(i) for i in params.get('range', ['0-0'])[0].split('-')]
            return { 'start' : start, 'end' : end }
        except Exception, e:
            pass
    return { 'start' : start, 'end' : end }

def get_youtube_video_range_from_path(path):
    start, end = 0, 0
    for regex in [YOUTUBE_VIDEO_RANGE_EXTRACT_REGEX, YOUTUBE_VIDEO_RANGE_EXTRACT_REGEX2]:
        match = regex.search(path)
        if match and len(match.groups()) == 2:
            try:
                start, end = int(match.groups()[0]), int(match.groups()[1])
                return { 'start' : start, 'end' : end }
            except Exception, e:
                pass
    return { 'start' : start, 'end' : end }

def get_youtube_video_range_from_query_or_path(query, path):
    range_info = get_youtube_video_range_from_query(query)
    if range_info['start'] == 0 and range_info['end'] == 0: range_info = get_youtube_video_range_from_path(path)
    return range_info

def get_youtube_video_range(url):
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_range_from_query_or_path(query, path)

# cpn, upn, range or video_id
def get_youtube_video_info_from_query_or_path(query, path, fields = []):
    info = {}
    if 'cpn' in fields: info['cpn'] = get_youtube_cpn_from_query_or_path(query, path)
    if 'upn' in fields: info['upn'] = get_youtube_upn_from_query_or_path(query, path)
    if 'video_id' in fields: info['video_id'] = get_youtube_video_id_from_query_or_path(query, path)
    if 'range' in fields: info['range'] = get_youtube_video_range_from_query_or_path(query, path)
    if 'format' in fields: info['format'] = get_youtube_video_format_from_query_or_path(query, path)
    return info

def get_youtube_video_info(url, fields = []):
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_info_from_query_or_path(query, path, fields)

# filename
def get_youtube_filenames(o, video_id, fmt, params = {}):
    suffix, ext, start, end = '', o.youtube_formats.get(fmt, {'ext' : ''}).get('ext', ''), params.get('start', 0), params.get('end', 0)
    if end != 0: suffix = '_%d_%d' % (start, end)
    if fmt != '': fmt = '_' + fmt
    filenames = [video_id + fmt + suffix + ext]
    if ext != '' and params.get('ext_opt', True): filenames += [video_id + fmt + suffix]
    return filenames

# cached_url
def youtube_cached_url(o, video_id, website_id, fmt, params = {}):
    valid_fmts = [fmt]

    if o.enable_youtube_html5_videos == 0:
        valid_fmts = filter(lambda fmt: o.youtube_formats[fmt]['cat'] not in ['webm', 'webm_3d'], valid_fmts)
    if o.enable_youtube_3d_videos == 0:
        valid_fmts = filter(lambda fmt: o.youtube_formats[fmt]['cat'] not in ['regular_3d', 'webm_3d'], valid_fmts)

    for fmt in set(valid_fmts):
        found, filename, cache_dir, size, index = search_youtube_video(o, video_id, website_id, fmt, params)
        if found:
            cached_url = o.redirect_code + ':' + os.path.join(o.cache_url, o.cache_alias, index, o.website_cache_dir[website_id], filename)
            return (True, filename, cache_dir, size, index, cached_url)
    return (False, '', '', '-', '', '')

# search video
def search_youtube_video(o, video_id, website_id, fmt, params = {}):
    index, size = '', '-'
    filenames = get_youtube_filenames(o, video_id, fmt, params)
    for website_dir in o.base_dirs[website_id]:
        for filename in filenames:
            try:
                video_path = os.path.join(website_dir, filename)
                if os.path.isfile(video_path):
                    if o.calculate_file_size: size = os.path.getsize(video_path)
                    if len(o.base_dirs[website_id]) > 1: index = str(o.base_dirs[website_id].index(website_dir))
                    return (True, filename, website_dir.rstrip(o.website_cache_dir[website_id]), size, index)
            except Exception, e:
                continue
    return (False, None, '', '-', '')

def is_youtube_domain(host):
    for domain in YOUTUBE_DOMAINS:
        if host.find(domain) > -1:
            for deny_domain in YOUTUBE_DOMAINS_DENY:
                if host.find(deny_domain) > -1:
                    return False
            return True
    return False

def check_youtube_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue, report_hit = True, 'youtube', None, '', True, True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    format = get_youtube_video_format_from_query_or_path(query, path)

    if is_youtube_domain(host):
        # Actual video content
        if path.find('videoplayback') > -1 and path.find('get_video_info') < 0:
            video_id = get_youtube_video_id_from_query_or_path(query, path)
            if get_youtube_video_range_from_query_or_path(query, path)['start'] > o.youtube_range_min_start: queue = False
        # Normal youtube videos in web browser
        elif path.find('stream_204') > -1 or (path.find('get_video') > -1 or path.find('watch_popup') > -1 or path.find('user_watch') > -1 or path.find('get_ad_tags') > -1 or path.find('get_video_info') > -1 or path.find('player_204') > -1 or path.find('ptracking') > -1 or path.find('set_awesome') > -1 or path == 's') and path.find('get_video_info') < 0:
            video_id = get_youtube_video_id_from_query_or_path(query, path)
            search, queue, report_hit = False, False, False
        elif path.find('api/stats/') > -1 and (path.find('/delayplay') > -1 or path.find('/atr') > -1 or path.find('/playback') > -1 or path.find('/watchtime') > -1):
            video_id = get_youtube_video_id_from_query_or_path(query, path)
            search, queue, report_hit = False, False, False
        # Embedded youtube videos
        elif YOUTUBE_VIDEO_ID_EXTRACT_REGEX1.search(path) and path.find('get_video_info') < 0:
            search = False
            try:
                video_id = YOUTUBE_VIDEO_ID_EXTRACT_REGEX1.search(path).group(2)
            except Exception, e:
                pass
        # Mobile API requests
        elif YOUTUBE_VIDEO_ID_EXTRACT_REGEX2.search(path):
            search = False
            try:
                video_id = YOUTUBE_VIDEO_ID_EXTRACT_REGEX2.search(path).group(1)
            except Exception, e:
                pass
        else:
            matched = False
    else:
        matched = False

    if format in o.youtube_skip_caching_itags:
        queue = False
    queue = False #TODO Temporary disabling youtube background caching
    return (matched, website_id, video_id, format, search, queue, report_hit)
