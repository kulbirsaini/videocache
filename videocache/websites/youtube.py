#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import cgi
import re
import urlparse

# Functions related to Youtube video ID and video format
def get_youtube_video_id_from_query(query):
    dict = cgi.parse_qs(query)
    if 'video_id' in dict:
        video_id = dict['video_id'][0]
    elif 'docid' in dict:
        video_id = dict['docid'][0]
    elif 'id' in dict:
        video_id = dict['id'][0]
    elif 'v' in dict:
        video_id = dict['v'][0]
    else:
        video_id = None
    return video_id

def get_youtube_video_id(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_id_from_query(query)

def get_youtube_video_format_from_query(query):
    dict = cgi.parse_qs(query)
    if 'itag' in dict:
        format = dict['itag'][0]
    elif 'fmt' in dict:
        format = dict['fmt'][0]
    elif 'layout' in dict and dict['layout'][0].lower() == 'mobile':
        format = '18'
    else:
        format = 34
    try:
        format = int(format)
    except:
        format = 34
    return int(format)

def get_youtube_video_format(url):
    """Youtube Specific"""
    fragments = urlparse.urlsplit(url)
    [host, path, query] = [fragments[1], fragments[2], fragments[3]]

    return get_youtube_video_format_from_query(query)

def check_youtube_video(host, path, query, url):
    matched, website_id, video_id, format, search, queue = True, 'youtube', None, '', True, True

    if get_youtube_video_format_from_query(query) == 18: format = '_18.mp4'

    # Normal youtube videos in web browser
    if (path.find('get_video') > -1 or path.find('watch') > -1 or path.find('watch_popup') > -1) and path.find('get_video_info') < 0 and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
        video_id = get_youtube_video_id_from_query(query)
        search = False
    # Embedded youtube videos
    elif re.compile('\/(v|e|embed)\/([0-9a-zA-Z_-]{11})').search(path) and path.find('get_video_info') < 0 and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
        search = False
        try:
            video_id = re.compile('\/(v|e|embed)\/([0-9a-zA-Z_-]{11})').search(path).group(2)
        except Exception, e:
            pass
    # Mobile API requests
    elif re.compile('\/feeds\/api\/videos\/[0-9a-zA-Z_-]{11}\/').search(path) and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
        format = '_18.mp4'
        search = False
        try:
            video_id = re.compile('\/feeds\/api\/videos\/([0-9a-zA-Z_-]{11})\/').search(path).group(1)
        except Exception, e:
            pass
    # Actual video content
    elif path.find('videoplayback') > -1 and path.find('get_video_info') < 0 and (host.find('youtu.be') > -1 or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.com').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]').search(host) or re.compile('\.(youtube|google|googlevideo|youtube-nocookie)\.[a-z][a-z]\.[a-z][a-z]').search(host)):
        queue = False
        video_id = get_youtube_video_id_from_query(query)
    else:
        matched = False

    return (matched, website_id, video_id, format, search, queue)

