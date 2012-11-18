#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from common import *
from error_codes import *

import logging
import os
import sqlite3
import time
import traceback

def initialize_database(options, pid = None):
    global o, process_id, db_cursor, db_connection
    o = options
    if not pid:
        process_id = os.getpid()
    else:
        process_id = pid
    try:
        db_connection = sqlite3.connect(options.filelistdb_path)
        db_cursor = db_connection.cursor()
    except Exception, e:
        ent({ 'code' : FILEDB_CONNECT_ERR, 'message' : 'Could not connect to sqlite database used for hashing video files.', 'debug' : str(e) })
        return None
    VideoFile.set_table_name(options.video_file_table_name)

def close_db_connection():
    db_connection.close()

class DB:
    @classmethod
    def get_table_names(klass):
        return map(lambda row: row[0], db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall())

    @classmethod
    def table_exists(klass, table_name):
        if table_name in klass.get_table_names():
            return True
        return False

    @classmethod
    def create_table(klass, table_name, query):
        if not klass.table_exists(table_name):
            db_cursor.execute(query)
            db_connection.commit()
        return True

class Model(object):
    # Class variables
    # fields
    # db_cursor
    # db_connection
    # table_name

    function_template_find_by = """
@classmethod
def find_by_%s(klass, value):
    return klass.find_by({ '%s' : value })
    """

    @classmethod
    def filter_params(klass, params, drop = []):
        keys = filter(lambda x: x in klass.fields and x not in drop, params.keys())
        values = map(lambda x: params[x], keys)
        return (keys, values)

    def update_attribute(self, attribute, value):
        if attribute in self.fields and attribute != 'id':
            query = "UPDATE %s SET %s = ? WHERE id = ?" % (self.table_name, attribute)
            db_cursor.execute(query, [value, self.id])
            db_connection.commit()
            return True
        return False

    def update_attributes(self, params):
        keys, values = self.filter_params(params, ['id'])
        if len(keys) == 0:
            return False
        values.append(self.id)
        query = "UPDATE %s SET " % self.table_name
        query += ', '.join(map(lambda x: x + ' = ? ', keys)) + " WHERE id = ? "
        db_cursor.execute(query, values)
        db_connection.commit()
        return True

    def destroy(self):
        query = "DELETE FROM %s WHERE id = ?" % self.table_name
        db_cursor.execute(query, (self.id, ))
        db_connection.commit()
        return True

    @classmethod
    def count(klass, params = {}):
        keys, values = klass.filter_params(params)
        return db_cursor.execute('SELECT COUNT(*) FROM %s' % klass.table_name).fetchone()[0]

    @classmethod
    def find_by(klass, params = {}):
        order = params.get('order', None)
        limit = params.get('limit', None)
        offset = params.get('offset', None)
        query_suffix = ''
        if order: query_suffix += " ORDER BY %s" % order
        if limit: query_suffix += " LIMIT %s" % limit
        if offset: query_suffix += " OFFSET %s" % offset
        keys, values = klass.filter_params(params)
        query = 'SELECT * FROM %s ' % klass.table_name
        if len(keys) != 0:
            query += ' WHERE ' + ' AND '.join(map(lambda x: x + ' = ? ', keys))
        query += query_suffix
        return map(lambda row: klass(row), db_cursor.execute(query, values).fetchall())

    @classmethod
    def find(klass, id):
        result = klass.find_by({ 'id' : id, 'limit' : 1 })
        if len(result) == 0:
            return None
        return result[0]

    @classmethod
    def first(klass, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id ASC')
        results = klass.find_by(params)
        if params['limit'] == 1 and len(results) == 0: return None
        if len(results) == 1: return results[0]
        return results

    @classmethod
    def last(klass, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id DESC')
        results = klass.find_by(params)
        if params['limit'] == 1 and len(results) == 0: return None
        if len(results) == 1: return results[0]
        return results

    @classmethod
    def all(klass,params = {}):
        return klass.find_by(params)

    @classmethod
    def create(klass, params):
        keys, values = klass.filter_params(params)
        if len(keys) == 0:
            return False
        keys = map(lambda x: '"' + x + '"', keys)
        query = "INSERT INTO %s " % klass.table_name
        query += " ( " + ', '.join(keys) + " ) VALUES ( " + ', '.join(['?'] * len(values)) + " ) "
        db_cursor.execute(query, values)
        db_connection.commit()
        return True

class VideoFile(Model):
    fields = ['id', 'cache_dir', 'website_id', 'filename', 'size', 'access_time', 'access_count']
    unique_fields = [ 'cache_dir', 'website_id', 'filename' ]
    for field in fields:
        exec((Model.function_template_find_by % (field, field)).strip())

    def __init__(self, attributes):
        self.id = attributes[0]
        self.cache_dir = attributes[1]
        self.website_id = attributes[2]
        self.filename = attributes[3]
        self.size = attributes[4]
        self.access_time = attributes[5]
        self.access_count = attributes[6]
        self.filepath = os.path.join(self.cache_dir, self.website_id, self.filename)

    @classmethod
    def set_table_name(klass, table_name):
        klass.table_name = table_name

    @classmethod
    def create_table(klass):
        query = 'create table %s (id INTEGER PRIMARY KEY AUTOINCREMENT, cache_dir STRING, website_id STRING, filename STRING, size INTEGER, access_time INTEGER, access_count INTEGER)' % klass.table_name
        return DB.create_table(klass.table_name, query)

    def to_s(self):
        print (self.id, self.cache_dir, self.website_id, self.filename, self.size, self.access_time, self.access_count)

    @classmethod
    def create(klass, params):
        uniq_key_params = {}
        map(lambda key: uniq_key_params.update({ key : params[key] }), filter(lambda x: x in klass.unique_fields, params))
        if len(params) == 0 or len(uniq_key_params) == 0:
            return False
        result = klass.first(uniq_key_params)
        if result:
            result.update_attributes({ 'access_count' : result.access_count + 1, 'access_time' : current_time() })
        else:
            super(VideoFile, klass).create(params)

def info(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.INFO), 'process_id' : process_id})
        o.vc_logger.info(build_message(params))

def error(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.ERROR), 'process_id' : process_id})
        o.vc_logger.error(build_message(params))

def warn(params = {}):
    if o.enable_videocache_log:
        params.update({ 'logformat' : o.logformat, 'timeformat' : o.timeformat, 'levelname' : logging.getLevelName(logging.WARN), 'process_id' : process_id})
        o.vc_logger.debug(build_message(params))

def trace(params = {}):
    if o.enable_trace_log:
        params.update({ 'logformat' : o.trace_logformat, 'timeformat' : o.timeformat, 'process_id' : process_id })
        o.trace_logger.info(build_message(params))

def ent(params = {}):
    error(params)
    params.update({ 'message' : traceback.format_exc() })
    trace(params)

def wnt(params = {}):
    error(params)
    params.update({ 'message' : traceback.format_exc() })
    trace(params)

def current_time():
    return int(time.time())

def create_tables():
    return VideoFile.create_table()

def report_file_access(cache_dir, website_id, filename, size, access_time = current_time(), access_count = 1):
    if o.log_filedb_activity:
        info({ 'code' : FILEDB_WRITE, 'website_id' : website_id, 'video_id' : filename, 'size' : size, 'message' : 'cache_dir : ' + cache_dir })
    try:
        VideoFile.create({ 'cache_dir' : cache_dir, 'website_id' : website_id, 'filename' : filename, 'size' : size, 'access_time' : access_time, 'access_count' : access_count })
    except Exception, e:
        ent({ 'code' : FILEDB_REPORT_ERR, 'website_id' : website_id, 'video_id' : filename, 'message' : 'Error occurred while registering file access to filelist database.', 'debug' : str(e) })
