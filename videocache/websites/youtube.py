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
import urllib
import urlparse

VALIDATE_YOUTUBE_VIDEO_ID_REGEX = re.compile('^[a-zA-Z0-9_\-]+$')
VALIDATE_YOUTUBE_DOMAIN_REGEX = re.compile('\.(youtube|youtube-nocookie)\.com')
YOUTUBE_VIDEO_ID_EXTRACT_REGEX1 = re.compile('\/(v|e|embed)\/([0-9a-zA-Z_-]{11})')
YOUTUBE_VIDEO_ID_EXTRACT_REGEX2 = re.compile('\/feeds\/api\/videos\/([0-9a-zA-Z_-]{11})\/')
YOUTUBE_VIDEO_ID_EXTRACT_REGEX3 = re.compile('\/(id|video_id|docid|v)\/([a-zA-Z0-9_\-]+)\/')
YOUTUBE_CPN_EXTRACT_REGEX = re.compile('\/cpn\/([a-zA-Z0-9_\-]+)\/')
YOUTUBE_FORMAT_EXTRACT_REGEX = re.compile('\/(itag|fmt)\/([0-9]+)\/')
YOUTUBE_VIDEO_RANGE_EXTRACT_REGEX = re.compile('\/range\/([0-9]+)-([0-9]+)\/')

# Functions related to Youtube video ID and video format
def get_youtube_video_id_from_query_or_path(query, path):
    params = cgi.parse_qs(query)
    video_id = ''
    if 'video_id' in params and VALIDATE_YOUTUBE_VIDEO_ID_REGEX.match(params['video_id'][0]) and len(params['video_id'][0]) <= 56:
        video_id = params['video_id'][0]
    elif 'docid' in params and VALIDATE_YOUTUBE_VIDEO_ID_REGEX.match(params['docid'][0]) and len(params['docid'][0]) <= 56:
        video_id = params['docid'][0]
    elif 'id' in params and VALIDATE_YOUTUBE_VIDEO_ID_REGEX.match(params['id'][0]) and len(params['id'][0]) <= 56:
        video_id = params['id'][0]
    elif 'v' in params and VALIDATE_YOUTUBE_VIDEO_ID_REGEX.match(params['v'][0]) and len(params['v'][0]) <= 56:
        video_id = params['v'][0]
    else:
        match = YOUTUBE_VIDEO_ID_EXTRACT_REGEX3.search(path)
        if match and len(match.groups()) == 2:
            video_id = match.groups()[1]

    video_id = urllib.quote(video_id)
    if video_id == '': video_id = None
    return video_id

def get_youtube_cpn_from_query_or_path(query, path):
    params = cgi.parse_qs(query)
    cpn = ''
    if 'cpn' in params:
        cpn = params['cpn'][0]
    else:
        match = YOUTUBE_CPN_EXTRACT_REGEX.search(path)
        if match and len(match.groups()) == 1:
            cpn = match.groups()[0]

    if cpn == '': cpn = None
    return cpn

def get_youtube_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_id_from_query_or_path(query, path)

def get_youtube_cpn(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_cpn_from_query_or_path(query, path)

def get_youtube_video_id_and_cpn(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return [ get_youtube_video_id_from_query_or_path(query, path), get_youtube_cpn_from_query_or_path(query, path) ]

def get_youtube_video_format_from_query_or_path(query, path):
    params = cgi.parse_qs(query)
    format = ''
    if 'itag' in params:
        format = params['itag'][0]
    elif 'fmt' in params:
        format = params['fmt'][0]
    elif 'layout' in params and params['layout'][0].lower() == 'mobile':
        format = '18'
    else:
        match = YOUTUBE_FORMAT_EXTRACT_REGEX.search(path)
        if match and len(match.groups()) == 2:
            format = match.groups()[1]

    return format

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_format_from_query_or_path(query, path)

def get_youtube_video_range_from_query_or_path(query, path):
    params = cgi.parse_qs(query)
    start = end = 0
    if 'range' in params:
        try:
            start, end = [int(i) for i in params.get('range', ['0-0'])[0].split('-')]
        except Exception, e:
            pass
    else:
        match = YOUTUBE_VIDEO_RANGE_EXTRACT_REGEX.search(path)
        if match and len(match.groups()) == 2:
            try:
                start, end = int(match.groups()[0]), int(match.groups()[1])
            except Exception, e:
                pass
    return { 'start' : start, 'end' : end }

def get_youtube_video_range(url):
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_range_from_query_or_path(query, path)

def get_youtube_filename(o, video_id, format, bit_range = {}):
    fmt = ext = suffix = ''
    start, end = bit_range.get('start', 0), bit_range.get('end', 0)

    if format != '':
        fmt = '_' + format
        if o.enable_youtube_partial_caching and end != 0: suffix = '_' + str(start) + '_' + str(end)
    if o.youtube_formats.has_key(format): ext = o.youtube_formats[format]['ext']
    return video_id + fmt + suffix + ext

def youtube_cached_url(o, video_id, website_id, format, params = {}):
    strict_mode = params.get('strict_mode', False)
    cache_check_only = params.get('cache_check_only', False)
    found, dir, size, index, cached_url = False, '', '-', '', ''
    valid_fmts = [format]
    if not cache_check_only:
        valid_fmts += ['']
    if not strict_mode and o.youtube_formats.has_key(format):
        if o.enable_youtube_format_support == 1:
            cat = o.youtube_formats[format]['cat']
            formats = filter(lambda fmt: o.youtube_formats[fmt]['res'] <= o.max_youtube_video_quality, o.youtube_itag_order[cat][o.youtube_itag_order[cat].index(format):])
            format in formats and formats.remove(format)
            valid_fmts += formats
        elif o.enable_youtube_format_support == 2:
            pass
        elif o.enable_youtube_format_support == 3:
            format_group = filter(lambda fmt_group: format in fmt_group, o.youtube_itag_groups)
            if len(format_group) != 0:
                format_group[0].remove(format)
                valid_fmts += format_group[0]

    if o.enable_youtube_html5_videos == 0:
        valid_fmts = filter(lambda fmt: o.youtube_formats[fmt]['cat'] not in ['webm', 'webm_3d'], valid_fmts)
    if o.enable_youtube_3d_videos == 0:
        valid_fmts = filter(lambda fmt: o.youtube_formats[fmt]['cat'] not in ['regular_3d', 'webm_3d'], valid_fmts)

    for fmt in valid_fmts:
        found, filename, dir, size, index = search_youtube_video(o, video_id, website_id, fmt, params)
        if found:
            cached_url = o.redirect_code + ':' + os.path.join(o.cache_url, o.cache_alias, index, o.website_cache_dir[website_id], filename)
            return (True, filename, dir, size, index, cached_url)
    return (False, '', '', '-', '', '')

def search_youtube_video(o, video_id, website_id, format, params = {}):
    found, dir, size, index = False, '', '-', ''

    start, end, strict_mode = params.get('start', 0), params.get('end', 0), params.get('strict_mode', False)
    #if o.enable_youtube_partial_caching and end != 0: suffix = '_' + str(start) + '_' + str(end)

    filenames = [get_youtube_filename(o, video_id, format, params)]

    if not strict_mode and start < 2048 and end != 0:
        filenames += [get_youtube_filename(o, video_id, format)]

    for dir in o.base_dirs[website_id]:
        for filename in filenames:
            try:
                video_path = os.path.join(dir, filename)
                if os.path.isfile(video_path):
                    size = os.path.getsize(video_path)
                    os.utime(video_path, None)
                    if len(o.base_dirs[website_id]) > 1: index = str(o.base_dirs[website_id].index(dir))
                    return (True, filename, dir.rstrip(o.website_cache_dir[website_id]), size, index)
            except Exception, e:
                continue
    return (False, filename, '', '-', '')

def check_youtube_video(o, url, host = None, path = None, query = None):
    matched, website_id, video_id, format, search, queue = True, 'youtube', None, '', True, True

    if not (host and path and query):
        fragments = urlparse.urlsplit(url)
        [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    format = get_youtube_video_format_from_query_or_path(query, path)

    # Actual video content
    if path.find('videoplayback') > -1 and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.youtube-nocookie.com') > -1 or host.find('youtu.be') > -1):
        video_id = get_youtube_video_id_from_query_or_path(query, path)
        if get_youtube_video_range_from_query_or_path(query, path)['start'] > 2500000: queue = False
    # Normal youtube videos in web browser
    elif path.find('stream_204') > -1 and query.find('view=0') > -1 and (host.find('.youtube.com') > -1 or host.find('.youtube-nocookie.com') > -1 or host.find('youtu.be') > -1):
        video_id = get_youtube_video_id_from_query_or_path(query, path)
        search = False
    elif (path.find('get_video') > -1 or path.find('watch_popup') > -1 or path.find('user_watch') > -1) and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.youtube-nocookie.com') > -1 or host.find('youtu.be') > -1):
        video_id = get_youtube_video_id_from_query_or_path(query, path)
        search = False
    # Embedded youtube videos
    elif YOUTUBE_VIDEO_ID_EXTRACT_REGEX1.search(path) and path.find('get_video_info') < 0 and (host.find('.youtube.com') > -1 or host.find('.youtube-nocookie.com') > -1 or host.find('youtu.be') > -1):
        search = False
        try:
            video_id = YOUTUBE_VIDEO_ID_EXTRACT_REGEX1.search(path).group(2)
        except Exception, e:
            pass
    # Mobile API requests
    elif YOUTUBE_VIDEO_ID_EXTRACT_REGEX2.search(path) and (host.find('.youtube.com') > -1 or host.find('.youtube-nocookie.com') > -1 or host.find('youtu.be') > -1):
        search = False
        try:
            video_id = YOUTUBE_VIDEO_ID_EXTRACT_REGEX2.search(path).group(1)
        except Exception, e:
            pass
    else:
        matched = False

    if format in o.youtube_skip_caching_itags:
        queue = False
    return (matched, website_id, video_id, format, search, queue)

