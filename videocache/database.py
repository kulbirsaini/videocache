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

import datetime
import logging
import os
os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs/'
import MySQLdb
import time
import traceback

def get_db_connection(num_tries = 0):
    if num_tries > 3:
        return (None, None)
    try:
        db_connection = MySQLdb.connect(o.db_hostname, o.db_username, o.db_password, o.db_database)
        db_cursor = db_connection.cursor()
        db_connection.autocommit(True)
        db_connection.ping()
        return (db_connection, db_cursor)
    except Exception, e:
        try:
            if db_connection.errno() == 2006 or db_connection.errno() == 2013:
                time.sleep(2)
                get_db_connection(num_tries + 1)
        except:
            return (None, None)

def initialize_database(options, pid = None):
    global o, process_id
    o = options
    if not pid:
        process_id = os.getpid()
    else:
        process_id = pid
    VideoFile.set_table_name(options.video_file_table_name)

class Model(object):
    # Class variables
    # fields
    # table_name

    placeholders = { 'string' : "'%s'", 'integer' : "%s", 'timestamp' : "'%s'" }
    function_template_find_by = """
@classmethod
def find_by_%s(klass, value):
    return klass.find_by({ '%s' : value })
    """

    def __init__(self, attributes):
        map(lambda field: setattr(self, field, attributes.get(field, None)), self.fields.keys())

    def to_s(self):
        print map(lambda field: getattr(self, field), self.fields.keys())

    @classmethod
    def set_table_name(klass, table_name):
        klass.table_name = table_name

    @classmethod
    def filter_params(klass, params, drop = []):
        keys = filter(lambda x: x in klass.fields.keys() and x not in drop, params.keys())
        values = map(lambda x: params[x], keys)
        return (keys, values)

    @classmethod
    def construct_query(klass, keys, values):
        new_values = []
        query_strings = []
        for key, value in zip(keys, values):
            placeholder = klass.placeholders[klass.fields[key]]
            if isinstance(value, list):
                if len(value) == 0:
                    warn({ 'code' : 'BAD_QUERY', 'message' : 'Empty list supplied as value for one of the parameters', 'debug' : str(keys) + ' ' + str(values) })
                    return '', []
                query_strings.append(' ' + key + ' IN ( ' + ', '.join([placeholder] * len(value)) + ' ) ')
                if klass.fields[key] == 'timestamp':
                    map(lambda x: new_values.append(timestamp_to_datetime(x)), value)
                else:
                    map(lambda x: new_values.append(x), value)
            else:
                query_strings.append(' ' + key + ' = ' + placeholder + ' ')
                if klass.fields[key] == 'timestamp':
                    new_values.append(timestamp_to_datetime(value))
                else:
                    new_values.append(value)
        return ' AND '.join(query_strings), new_values

    def update_attribute(self, attribute, value):
        if attribute in self.fields.keys() and attribute != 'id':
            if attribute == 'access_time':
                value = timestamp_to_datetime(value)
            query = "UPDATE %s SET %s = " + self.placeholders[self.fields[attribute]]  + " WHERE id = %s "
            query = query % (self.table_name, attribute, value, self.id)
            db_connection, db_cursor = get_db_connection()
            if db_connection and db_cursor:
                db_cursor.execute(query)
                db_connection.close()
            return True
        return False

    def update_attributes(self, params):
        if params.has_key('access_time'):
            params['access_time'] = timestamp_to_datetime(params['access_time'])
        keys, values = self.filter_params(params, ['id'])
        if len(keys) == 0:
            return False
        values.append(self.id)
        query = "UPDATE %s SET " % self.table_name
        query += ', '.join(map(lambda x: x + ' = ' + self.placeholders[self.fields[x]] + ' ', keys)) + " WHERE id = %s "
        query = query % tuple(values)
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            db_connection.close()
        return True

    def destroy(self):
        query = "DELETE FROM %s WHERE id = %s" % (self.table_name, self.id )
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            db_connection.close()
        return True

    @classmethod
    def destroy(klass, params = {}):
        keys, values = klass.filter_params(params)
        where_part, values = klass.construct_query(keys, values)
        if len(values) < 1:
            return False
        query = ("DELETE FROM %s WHERE " % klass.table_name) + where_part
        query = query % tuple(values)
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            db_connection.close()
        return True

    @classmethod
    def count(klass, params = {}):
        keys, values = klass.filter_params(params)
        where_part, values = klass.construct_query(keys, values)
        query = "SELECT COUNT(*) FROM %s" % klass.table_name
        if where_part:
            query += ' WHERE ' + where_part % tuple(values)
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            result = db_cursor.fetchall()[0][0]
            db_connection.close()
            return result
        return 0

    @classmethod
    def find_by(klass, params = {}):
        order = params.get('order', None)
        limit = params.get('limit', None)
        offset = params.get('offset', None)
        select = params.get('select', ', '.join(klass.fields))
        if 'id' not in map(lambda x: x.strip(), select.split(',')):
            select = 'id, ' + select
        select_keys = map(lambda x: x.strip(), select.split(','))
        query_suffix = ''
        if order: query_suffix += " ORDER BY %s" % order
        if limit: query_suffix += " LIMIT %s" % limit
        if offset: query_suffix += " OFFSET %s" % offset
        keys, values = klass.filter_params(params)
        query = 'SELECT ' + select + ' FROM %s ' % klass.table_name
        if len(keys) != 0:
            where_part, values = klass.construct_query(keys, values)
            query += ' WHERE ' + where_part
        query += query_suffix
        query = query % tuple(values)
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            results = db_cursor.fetchall()
            db_connection.close()
        else:
            results = []
        return map(lambda row: klass(dict(zip(select_keys, row))), results)

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
        query = "INSERT INTO %s " % klass.table_name
        query += " ( " + ', '.join(keys) + " ) VALUES ( " + ', '.join(map(lambda x: klass.placeholders[klass.fields[x]], keys)) + " ) "
        query = query % tuple(values)
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            db_connection.close()
        return True

    @classmethod
    def execute(klass, query):
        db_connection, db_cursor = get_db_connection()
        if db_connection and db_cursor:
            db_cursor.execute(query)
            results = db_cursor.fetchall()
            db_connection.close()
            return results
        return []

class VideoFile(Model):
    fields = { 'id' : 'integer', 'cache_dir' : 'string', 'website_id' : 'string', 'filename' : 'string', 'size' : 'integer', 'access_time' : 'timestamp', 'access_count' : 'integer' }
    unique_fields = [ 'cache_dir', 'website_id', 'filename' ]
    for field in fields:
        exec((Model.function_template_find_by % (field, field)).strip())

    def __init__(self, attributes):
        Model.__init__(self, attributes)
        if self.access_time:
            self.access_time = datetime_to_timestamp(self.access_time)
        if self.cache_dir and self.website_id and self.filename:
            self.filepath = os.path.join(self.cache_dir, o.website_cache_dir[self.website_id], self.filename)
        else:
            self.filepath = None

    @classmethod
    def create_table(klass):
        try:
            db_connection, db_cursor = get_db_connection()
            if db_connection and db_cursor:
                # Create Tables
                db_cursor.execute('SHOW TABLES')
                tables = map(lambda result: result[0], db_cursor.fetchall())
                query = 'CREATE TABLE IF NOT EXISTS %s (id BIGINT PRIMARY KEY AUTO_INCREMENT, cache_dir VARCHAR(128), website_id VARCHAR(32), filename VARCHAR(512), size INT DEFAULT 0, access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP, access_count INT DEFAULT 1)' % klass.table_name
                if klass.table_name not in tables: db_cursor.execute(query)

                # Create indices
                db_cursor.execute('SHOW INDEX FROM %s' % klass.table_name)
                indices = map(lambda result: result[2], db_cursor.fetchall())
                if 'cwf_index' not in indices: db_cursor.execute('CREATE UNIQUE INDEX cwf_index ON %s (cache_dir, website_id, filename(192))' % klass.table_name)
                if 'cache_dir_index' not in indices: db_cursor.execute('CREATE INDEX cache_dir_index ON %s (cache_dir)' % klass.table_name)
                if 'access_time_index' not in indices: db_cursor.execute('CREATE INDEX access_time_index ON %s (access_time)' % klass.table_name)
                if 'access_count_index' not in indices: db_cursor.execute('CREATE INDEX access_count_index ON %s (access_count)' % klass.table_name)
                if 'size_index' not in indices: db_cursor.execute('CREATE INDEX size_index ON %s (size)' % klass.table_name)
                db_connection.close()
            else:
                print 'Could not connect to database'
                return False
        except:
            return False
        return True

    @classmethod
    def create(klass, params):
        params['access_count'] = params.get('access_count', 1)
        params['access_time'] = params.get('access_time', current_time())
        if params.has_key('filename'):
            params['filename'] = str(params['filename'])
        if params.has_key('access_time'):
            params['access_time'] = timestamp_to_datetime(params['access_time'])
        keys, values = klass.filter_params(params)
        if len(keys) == 0:
            return False
        query = "INSERT INTO %s " % klass.table_name
        query += " ( " + ', '.join(keys) + " ) VALUES ( " + ', '.join(map(lambda x: klass.placeholders[klass.fields[x]], keys)) + " ) "
        query = query % tuple(values)
        query += " ON DUPLICATE KEY UPDATE access_count = access_count + 1, access_time = CURRENT_TIMESTAMP"
        VideoFile.execute(query)
        return True

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

def create_tables():
    return VideoFile.create_table()
