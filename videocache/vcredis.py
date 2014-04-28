#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *

try:
    import cPickle as pickle
except Exception, e:
    import pickle
import redis
import hiredis

# TODO Abstract to a generic class with sorted set and hash

class VideoFile(object):

    def __init__(self, o):
        self.redis = o.redis
        self.video_file_scores_key = 'video_file_scores'
        self.video_file_info_key = 'video_file_info'

    def get_video_file_score_by_key(self, key):
        score = self.redis.zscore(self.video_file_scores_key, key)
        if score:
            return (score // 1, 0)
        return (0,0)

    def get_video_file_score(self, website_id, video_id):
        return self.get_video_file_info_by_key(website_id + ':' + video_id)

    def set_video_file_score_by_key(self, key, score, access_time = None):
        if not access_time:
            access_time = int(time.time())
        score = str(score) + '.' + str(access_time)
        self.redis.zadd(self.video_file_scores_key, key, score)

    def set_video_file_score(self, website_id, video_id, score = 1, access_time = None):
        self.set_video_file_score_by_key(website_id + ':' + video_id, score, access_time)

    def increment_video_file_score_by_key(self, key, incr = 1, access_time = None):
        score = self.get_video_file_score_by_key(key)[0]
        self.set_video_file_score_by_key(key, score + incr, access_time)

    def increment_video_file_score(self, website_id, video_id, incr = 1, access_time = None):
        self.increment_video_file_score_by_key(website_id + ':' + video_id, incr, access_time)

    # key can be single item or a list
    def remove_video_file_score_by_key(self, key):
        self.redis.zrem(self.video_file_scores_key, key)

    def remove_video_file_score(self, website_id, video_id):
        self.remove_video_file_score_by_key(website_id + ':' + video_id)

    def get_least_used_video_files(self, limit = 1000, offset = 0):
        if limit != -1: limit = offset + limit
        return self.redis.zrange(self.video_file_scores_key, 0, limit)

    def get_video_file_info_by_key(self, key):
        info = self.redis.hget(self.video_file_info_key, key)
        if info:
            return pickle.loads(info)
        return None

    def get_video_file_info_by_keys(self, keys):
        if len(keys) == 0: return []
        infos = self.redis.hmget(self.video_file_info_key, keys)
        return [pickle.loads(info) if info is not None else None for info in infos]

    def get_video_file_info(self, website_id, video_id):
        return self.get_video_file_info_by_key(website_id + ':' + video_id)

    def get_bulk_video_file_info(self, keys):
        return self.get_video_file_info_by_keys(keys)

    def set_video_file_info_by_key(self, key, info):
        return self.redis.hset(self.video_file_info_key, key, pickle.dumps(info))

    def set_video_file_info(self, website_id, video_id, info):
        return self.set_video_file_info_by_key(website_id + ':' + video_id, info)

    # key can be single item or a list
    def remove_video_file_info_by_key(self, key):
        return self.redis.hdel(self.video_file_info_key, key)

    def remove_video_file_info(self, website_id, video_id):
        return self.remove_video_file_info_by_key(website_id + ':' + video_id)

    # key can be single item or a list
    def remove_video_file_by_key(self, key):
        self.remove_video_file_score_by_key(key)
        self.remove_video_file_info_by_key(key)

    def remove_video_file(self, website_id, video_id):
        self.remove_video_file_by_key(website_id + ':' + video_id)


class VideoQueue(object):

    def __init__(self, o):
        self.redis = o.redis
        self.video_queue_scores_key = 'video_queue_scores'
        self.video_queue_info_key = 'video_queue_info'


class ActiveVideoQueue(object):

    def __init__(self, o):
        self.redis = o.redis
        self.active_video_queu_info_key = 'active_video_queue_info'


class YoutubeCPN(object):

    def __init__(self, o):
        self.redis = o.redis
        self.cpn_scores_key = 'cpn_scores'
        self.long_id_scores_key = 'long_id_scores'
        self.cpn_map_key = 'cpn_map'
        self.long_id_map_key = 'long_id_map'

