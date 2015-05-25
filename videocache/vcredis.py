#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs/'

from common import *
from redis.exceptions import ConnectionError

import redis
import hiredis
import time
import traceback

class VideoCacheRedis(object):

    def __init__(self, o):
        self.o = o
        self.process_id = os.getpid()
        self.redis = o.redis
        self.error_messages = { 'connection' : 'Error while connecting to redis. Please check if redis-server daemon is running. Look for related configuration in /etc/videocache.conf', 'general' : 'Error executing redis command. Please report with trace if you see these errors frequently.' }
        return

    # Logging
    def error(self, params = {}):
        if self.o.enable_scheduler_log and self.o.vcs_logger:
            params.update({ 'logformat' : self.o.scheduler_logformat, 'timeformat' : self.o.timeformat, 'levelname' : LOG_LEVEL_ERR, 'process_id' : self.process_id })
            self.o.vcs_logger.error(build_message(params))

    def trace(self, params = {}):
        if self.o.enable_trace_log and self.o.trace_logger:
            params.update({ 'logformat' : self.o.trace_logformat, 'timeformat' : self.o.timeformat, 'process_id' : self.process_id })
            self.o.trace_logger.info(build_message(params))

    def ent(self, params = {}):
        self.error(params)
        params.update({ 'message' : traceback.format_exc() })
        self.trace(params)

    # General
    def ping(self):
        try:
            return self.redis.ping()
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return False

    # Keys methods
    def delete(self, key):
        try:
            return self.redis.delete(key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def keys(self, pattern):
        try:
            return self.redis.keys(pattern)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    def exists(self, key):
        try:
            return self.redis.exists(key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return False

    def rename(self, old_key, new_key):
        try:
            return self.exists(old_key) and self.redis.renamex(old_key, new_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return False


    # Hash methods
    # Multiple fields as arguments
    def hdel(self, db_key, field):
        if field == []: return 0
        try:
            return self.redis.hdel(db_key, *(self.flatten(field)))
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def hexists(self, db_key, field):
        try:
            return self.redis.hexists(db_key, field)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return False

    def hget(self, db_key, field):
        try:
            return self.redis.hget(db_key, field)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return None

    def hmget(self, db_key, fields):
        if fields == []: return []
        try:
            return self.redis.hmget(db_key, *(self.flatten(fields)))
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    def hgetall(self, db_key):
        try:
            return self.redis.hgetall(db_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return {}

    def hkeys(self, db_key):
        try:
            return self.redis.hkeys(db_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    def hlen(self, db_key):
        try:
            return self.redis.hlen(db_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def hset(self, db_key, field, value):
        if db_key == None: return 0
        try:
            return self.redis.hset(db_key, field, value)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    # Set methods
    # Multiple members as arguments
    def sadd(self, db_key, member):
        if db_key == None: return 0
        if member == []: return 0
        try:
            return self.redis.sadd(db_key, *(self.flatten(member)))
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def scard(self, db_key):
        try:
            return self.redis.scard(db_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def sismember(self, db_key, member):
        try:
            return self.redis.sismember(db_key, member)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return False

    def smembers(self, db_key):
        try:
            return self.redis.smembers(db_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    # Multiple members as arguments
    def srem(self, db_key, member):
        if member == []: return 0
        try:
            return self.redis.srem(db_key, *(self.flatten(member)))
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    # Sorted Set methods
    def zadd(self, db_key, *args):
        if db_key == None: return 0
        try:
            return self.redis.zadd(db_key, *(args))
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def zcard(self, db_key):
        try:
            return self.redis.zcard(db_key)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def zrange(self, db_key, start, stop, *args, **kwargs):
        try:
            return self.redis.zrange(db_key, start, stop, args, kwargs)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    def zrangebyscore(self, db_key, minimum, maximum):
        try:
            return self.redis.zrangebyscore(db_key, minimum, maximum)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    def zrank(self, db_key, member):
        try:
            return self.redis.zrank(db_key, member)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return None

    # Multiple members as arguments
    def zrem(self, db_key, member):
        if member == []: return 0
        try:
            return self.redis.zrem(db_key, *(self.flatten(member)))
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def zremrangebyrank(self, db_key, start, stop):
        try:
            return self.redis.zremrangebyrank(db_key, start, stop)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return 0

    def zrevrange(self, db_key, start, stop, *args, **kwargs):
        try:
            return self.redis.zrevrange(db_key, start, stop, args, kwargs)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return []

    def zscore(self, db_key, member):
        try:
            return self.redis.zscore(db_key, member)
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return None

    # Key encoding/decoding
    def key(self, website_id, video_id):
        try:
            return website_id + ':' + video_id
        except ConnectionError, ce:
            self.ent({ 'code' : 'REDIS_CONNECTION_ERR', 'message' : self.error_messages['connection'], 'debug' : str(ce) })
        except Exception, e:
            self.ent({ 'code' : 'REDIS_COMMAND_ERR', 'message' : self.error_messages['general'], 'debug' : str(e) })
        return None

    def decode_key(self, key):
        if not key: return (None, None)
        parts = key.split(':', 1)
        if len(parts) == 2:
            return (parts[0], parts[1])
        return (None, None)

    def _flatten(self, *args):
        for x in args:
            if hasattr(x, '__iter__'):
                for y in self._flatten(*x):
                    yield y
            else:
                yield x

    def flatten(self, *args):
        return list(self._flatten(*args))

class VideoFile(VideoCacheRedis):

    def __init__(self, o):
        self.scores_key_prefix = 'videocache:video_files:'
        VideoCacheRedis.__init__(self, o)
        return

    # Scores
    def get_score_by_key(self, redis_key, key):
        score = self.zscore(redis_key, key)
        if score:
            return (int(score//1), int((score - score//1) * 10000000000))
        return (0,0)

    def get_score(self, cache_dir, website_id, video_id):
        return self.get_score_by_key(self.redis_key(cache_dir, website_id), video_id)

    def set_score_by_key(self, redis_key, key, score = 1, access_time = None):
        if not access_time:
            access_time = int(time.time())
        score = str(score) + '.' + str(access_time)
        key = self.flatten([[i, score] for i in self.flatten(key)])
        if not key: return 0
        return self.zadd(redis_key, *(key))

    def set_score(self, cache_dir, website_id, video_id, score = 1, access_time = None):
        return self.set_score_by_key(self.redis_key(cache_dir, website_id), video_id, score, access_time)

    def increment_score_by_key(self, redis_key, key, incr = 1, access_time = None):
        score, timestamp = self.get_score_by_key(redis_key, key)
        if not access_time: access_time = timestamp
        return self.set_score_by_key(redis_key, key, score + incr, access_time)

    def increment_score(self, cache_dir, website_id, video_id, incr = 1, access_time = None):
        return self.increment_score_by_key(self.redis_key(cache_dir, website_id), video_id, incr, access_time)

    def remove_score_by_key(self, redis_key, key):
        return self.zrem(redis_key, key)

    def remove_score(self, cache_dir, website_id, video_id):
        return self.remove_score_by_key(self.redis_key(cache_dir, website_id), video_id)

    def length_by_website(self, website_id):
        count = 0
        for cache_dir in self.o.base_dir_list:
            count += self.zcard(self.redis_key(cache_dir, website_id))
        return count

    def length_by_cache_dir(self, cache_dir):
        count = 0
        for website_id in self.o.websites:
            count += self.zcard(self.redis_key(cache_dir, website_id))
        return count

    def length(self):
        count = 0
        for website_id in self.o.websites:
            for cache_dir in self.o.base_dir_list:
                count += self.zcard(self.redis_key(cache_dir, website_id))
        return count


    def score_exists_for_key(self, redis_key, key):
        if self.zrank(redis_key, key) == None:
            return False
        return True

    def score_exists(self, cache_dir, website_id, video_id):
        return self.score_exists_for_key(self.redis_key(cache_dir, website_id), video_id)

    def get_least_used(self, cache_dir, limit = 1000):
        videos = []
        for website_id in self.o.websites:
            videos += [(v, k, website_id) for k, v in self.zrange(self.redis_key(cache_dir, website_id), 0, limit, withscores=True)]
        if limit == -1:
            return sorted(videos)
        return sorted(videos)[:limit]

    def get_most_used(self, cache_dir, limit = 1000):
        videos = []
        for website_id in self.o.websites:
            videos += [(v, k, website_id) for k, v in self.zrange(self.redis_key(cache_dir, website_id), 0, limit, withscores=True)]
        if limit == -1:
            return sorted(videos, reverse = True)
        return sorted(videos, reverse = True)[:limit]

    def get_filenames_for_by_key(self, key, limit = -1):
        return self.zrange(key, 0, limit)

    def get_filenames_for(self, cache_dir, website_id):
        if not (cache_dir and website_id): return None
        return self.get_filenames_for_by_key(self.redis_key(cache_dir, website_id))

    def redis_key(self, cache_dir, website_id):
        if not (cache_dir and website_id): return None
        return self.scores_key_prefix + cache_dir + ":" + website_id

    def decode_redis_key(self, key):
        if not key: return (None, None)
        parts = key.split(":")
        if len(parts) == 4:
            return (parts[2], parts[3])
        return (None, None)

    def get_keys(self):
        return self.keys(self.scores_key_prefix + '*')


class VideoQueue(VideoCacheRedis):

    def __init__(self, o):
        self.scores_key = 'videocache:video_queue_scores'
        self.info_key = 'videocache:video_queue_info'
        VideoCacheRedis.__init__(self, o)
        return

    # Scores
    def set_score_by_key(self, key, score = 1, access_time = None):
        if not access_time: access_time = int(time.time())
        score = str(score) + '.' + str(access_time)
        return self.zadd(self.scores_key, *([key, score]))

    def set_score(self, website_id, video_id, fmt = '', score = 1, access_time = None):
        return self.set_score_by_key(self.key(website_id, video_id, fmt), score, access_time)

    def get_score_by_key(self, key):
        score = self.zscore(self.scores_key, key)
        if score:
            return (int(score//1), int((score - score//1) * 10000000000))
        return (0,0)

    def get_score(self, website_id, video_id, fmt):
        return self.get_score_by_key(self.key(website_id, video_id, fmt))

    def increment_score_by_key(self, key, incr = 1, access_time = None):
        score = self.get_score_by_key(key)[0]
        return self.set_score_by_key(key, score + incr, access_time)

    def increment_score(self, website_id, video_id, fmt = '', incr = 1, access_time = None):
        return self.increment_score_by_key(self.key(website_id, video_id, fmt), incr, access_time)

    def remove_score_by_key(self, key):
        return self.zrem(self.scores_key, key)

    def remove_score(self, website_id, video_id, fmt = ''):
        return self.remove_score_by_key(self.key(website_id, video_id, fmt))

    def get_score_length(self):
        return self.zcard(self.scores_key)

    # Video Info
    def add_info_by_key(self, key, info):
        self.increment_score_by_key(key)
        return self.hset(self.info_key, key, info)

    def add_info(self, website_id, video_id, fmt, info):
        return self.add_info_by_key(self.key(website_id, video_id, fmt), info)

    def get_info_by_key(self, key):
        return self.hget(self.info_key, key)

    def get_info(self, website_id, video_id, fmt = ''):
        return self.get_info_by_key(self.key(website_id, video_id, fmt))

    def remove_info_by_key(self, key):
        self.remove_score_by_key(key)
        return self.hdel(self.info_key, key)

    def remove_info(self, website_id, video_id, fmt = ''):
        return self.remove_info_by_key(self.key(website_id, video_id, fmt))

    def get_queue_length(self):
        return self.hlen(self.info_key)

    # Mining
    def get_popular(self):
        while True:
            video_id = self.zrevrange(self.scores_key, 0, 0)
            if not video_id: return (None, None, None, None)
            score, timestamp = self.get_score_by_key(video_id[0])
            if (score and score < self.o.hit_threshold) or (timestamp and (time.time() - timestamp) < self.o.log_hit_threshold):
                return (None, None, None, None)
            video_info = self.get_info_by_key(video_id[0])
            self.remove_info_by_key(video_id)
            if video_info:
                website_id, video_id, fmt = self.decode_key(video_id[0])
                return (website_id, video_id, fmt, video_info)
            time.sleep(0.02)

    def get_least_scoring_videos(self, spare = 100):
        return self.zrange(self.scores_key, 0, -spare)

    # Cleanup
    def flush(self):
        self.delete(self.scores_key)
        self.delete(self.info_key)
        return

    def expire_videos(self):
        video_ids = self.get_least_scoring_videos()
        self.remove_info_by_key(video_ids)
        return True

    # General
    def key(self, website_id, video_id, fmt = ''):
        return website_id + ':' + video_id + ':' + fmt

    def decode_key(self, key):
        if not key: return (None, None, None)
        parts = key.split(':', 1)
        if len(parts) == 2:
            part_parts = parts[1].rsplit(':', 1)
            if len(part_parts) == 2:
                return (parts[0], part_parts[0], part_parts[1])
        return (None, None, None)


class ActiveVideoQueue(VideoCacheRedis):

    def __init__(self, o):
        self.info_key = 'videocache:active_video_queue_info'
        VideoCacheRedis.__init__(self, o)
        return

    def add_video_by_key(self, key):
        return self.sadd(self.info_key, key)

    def add_video(self, website_id, video_id):
        return self.add_video_by_key(self.key(website_id, video_id))

    def is_video_in_queue_by_key(self, key):
        return self.sismember(self.info_key, key)

    def is_video_in_queue(self, website_id, video_id):
        return self.is_video_in_queue_by_key(self.key(website_id, video_id))

    def remove_video_by_key(self, key):
        return self.srem(self.info_key, key)

    def remove_video(self, website_id, video_id):
        return self.remove_video_by_key(self.key(website_id, video_id))

    def get_queue_length(self):
        return self.scard(self.info_key)

    def flush(self):
        return self.delete(self.info_key)


class AccessLogQueue(VideoCacheRedis):

    def __init__(self, o):
        self.queue_key = 'videocache:access_log:queue'
        VideoCacheRedis.__init__(self, o)
        return

    def push(self, url):
        if not url: return 0
        return self.zadd(self.queue_key, *([url, int(time.time())]))

    def pop(self):
        url = self.zrange(self.queue_key, 0, 0)
        if url:
            self.zrem(self.queue_key, url)
            return url[0]
        return None

    def length(self):
        return self.zcard(self.queue_key)

    def trim(self, spare = 50):
        return self.zremrangebyrank(self.queue_key, 0, self.length() - spare)

    def flush(self):
        return self.delete(self.queue_key)
