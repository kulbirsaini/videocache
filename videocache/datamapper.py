#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

import os

class DB:
    @classmethod
    def get_table_names(klass, o):
        return map(lambda row: row[0], o.db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall())

    @classmethod
    def table_exists(klass, o, table_name):
        if table_name in DB.get_table_names(o):
            return True
        return False

    @classmethod
    def create_table(klass, o, table_name, query = 'create table video_files (id INTEGER PRIMARY KEY AUTOINCREMENT, cache_dir STRING, filename STRING, size INTEGER, access_time INTEGER, access_count INTEGER)'):
        if not DB.table_exists(o, table_name):
            o.db_cursor.execute(query)
            o.db_connection.commit()
        return True

class VideoFile:
    fields = ['id', 'cache_dir', 'filename', 'size', 'access_time', 'access_count']

    def __init__(self, o, id, cache_dir, filename, size, access_time, access_count):
        self.o = o
        self.id = id
        self.cache_dir = cache_dir
        self.filename = filename
        self.size = size
        self.access_time = access_time
        self.access_count = access_count
        self.filepath = os.path.join(cache_dir, filename)

    @classmethod
    def filter_params(klass, params, drop = []):
        keys = filter(lambda x: x in VideoFile.fields and x not in drop, params.keys())
        values = map(lambda x: params[x], keys)
        return (keys, values)

    def update_attribute(self, attribute, value):
        if attribute in VideoFile.fields and attribute != 'id':
            query = "UPDATE %s SET %s = ? WHERE id = ?" % (self.o.video_file_table_name, attribute)
            self.o.db_cursor.execute(query, [value, self.id])
            self.o.db_connection.commit()
            return True
        return False

    def update_attributes(self, params):
        keys, values = VideoFile.filter_params(params, ['id'])
        if len(keys) == 0:
            return False
        values.append(self.id)
        query = "UPDATE %s SET " % self.o.video_file_table_name
        query += ', '.join(map(lambda x: x + ' = ? ', keys)) + " WHERE id = ? "
        self.o.db_cursor.execute(query, values)
        self.o.db_connection.commit()
        return True

    def destroy(self):
        query = "DELETE FROM %s WHERE id = ?" % self.o.video_file_table_name
        self.o.db_cursor.execute(query, (self.id, ))
        self.o.db_connection.commit()
        return True

    @classmethod
    def count(klass, o, params = {}):
        keys, values = VideoFile.filter_params(params)
        return o.db_cursor.execute('SELECT COUNT(*) FROM %s' % o.video_file_table_name).fetchone()[0]

    @classmethod
    def find(klass, o, id):
        query = 'SELECT * FROM %s ' % o.video_file_table_name
        row = o.db_cursor.execute(query + ' WHERE id = ?', (id,)).fetchone()
        if row:
            return VideoFile(o, row[0], row[1], row[2], row[3], row[4], row[5])
        return None

    @classmethod
    def find_by(klass, o, params = {}):
        order = params.get('order', None)
        limit = params.get('limit', None)
        offset = params.get('offset', None)
        query_suffix = ''
        if order: query_suffix += " ORDER BY %s" % order
        if limit: query_suffix += " LIMIT %s" % limit
        if offset: query_suffix += " OFFSET %s" % offset
        keys, values = VideoFile.filter_params(params)
        query = 'SELECT * FROM %s ' % o.video_file_table_name
        if len(keys) != 0:
            query += ' WHERE ' + ' AND '.join(map(lambda x: x + ' = ? ', keys))
        query += query_suffix
        return map(lambda row: VideoFile(o, row[0], row[1], row[2], row[3], row[4], row[5]), o.db_cursor.execute(query, values).fetchall())

    @classmethod
    def first(klass, o, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id ASC')
        video_files = VideoFile.find_by(o, params)
        if len(video_files) == 1:
            return video_files[0]
        return video_files

    @classmethod
    def last(klass, o, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id DESC')
        video_files = VideoFile.find_by(o, params)
        if len(video_files) == 1:
            return video_files[0]
        return video_files

    @classmethod
    def all(klass, o, params = {}):
        VideoFile.find_by(o, params)

    @classmethod
    def create(klass, o, params = {}):
        keys, values = VideoFile.filter_params(params)
        if len(keys) == 0:
            return False
        keys = map(lambda x: '"' + x + '"', keys)
        query = "INSERT INTO %s " % o.video_file_table_name
        query += " ( " + ', '.join(keys) + " ) VALUES ( " + ', '.join(['?'] * len(values)) + " ) "
        o.db_cursor.execute(query, values)
        o.db_connection.commit()
        return True
