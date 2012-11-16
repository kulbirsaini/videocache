#!/usr/bin/env python
#
# (C) Copyright White Magnet Software Private Limited
# Company Website : http://whitemagnet.com/
# Product Website : http://cachevideos.com/
#

__author__ = """Kulbir Saini <saini@saini.co.in>"""
__docformat__ = 'plaintext'

from vcoptions import VideocacheOptions

import os

o = VideocacheOptions()

class DB:
    db_cursor = o.db_cursor
    db_connection = o.db_connection
    @classmethod
    def get_table_names(klass):
        return map(lambda row: row[0], klass.db_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;").fetchall())

    @classmethod
    def table_exists(klass, table_name):
        if table_name in klass.get_table_names():
            return True
        return False

    @classmethod
    def create_table(klass, table_name, query):
        if not klass.table_exists(table_name):
            klass.db_cursor.execute(query)
            klass.db_connection.commit()
        return True

class Model:
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
            self.db_cursor.execute(query, [value, self.id])
            self.db_connection.commit()
            return True
        return False

    def update_attributes(self, params):
        keys, values = self.filter_params(params, ['id'])
        if len(keys) == 0:
            return False
        values.append(self.id)
        query = "UPDATE %s SET " % self.table_name
        query += ', '.join(map(lambda x: x + ' = ? ', keys)) + " WHERE id = ? "
        self.db_cursor.execute(query, values)
        self.db_connection.commit()
        return True

    def destroy(self):
        query = "DELETE FROM %s WHERE id = ?" % self.table_name
        self.db_cursor.execute(query, (self.id, ))
        self.db_connection.commit()
        return True

    @classmethod
    def count(klass, params = {}):
        keys, values = klass.filter_params(params)
        return klass.db_cursor.execute('SELECT COUNT(*) FROM %s' % klass.table_name).fetchone()[0]

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
        return map(lambda row: klass(row), klass.db_cursor.execute(query, values).fetchall())

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
        if len(results) == 1:
            return results[0]
        return results

    @classmethod
    def last(klass, params = {}):
        params['limit'] = params.get('limit', 1)
        params['order'] = params.get('order', 'id DESC')
        results = klass.find_by(params)
        if len(results) == 1:
            return results[0]
        return results

    @classmethod
    def all(klass,params = {}):
        return klass.find_by(params)

    @classmethod
    def create(klass, params = {}):
        keys, values = klass.filter_params(params)
        if len(keys) == 0:
            return False
        keys = map(lambda x: '"' + x + '"', keys)
        query = "INSERT INTO %s " % klass.table_name
        query += " ( " + ', '.join(keys) + " ) VALUES ( " + ', '.join(['?'] * len(values)) + " ) "
        klass.db_cursor.execute(query, values)
        klass.db_connection.commit()
        return True

class VideoFile(Model):
    fields = ['id', 'cache_dir', 'website_id', 'filename', 'size', 'access_time', 'access_count']
    db_cursor = o.db_cursor
    db_connection = o.db_connection
    table_name = o.video_file_table_name
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
    def create_table(klass):
        query = 'create table %s (id INTEGER PRIMARY KEY AUTOINCREMENT, cache_dir STRING, website_id STRING, filename STRING, size INTEGER, access_time INTEGER, access_count INTEGER)' % klass.table_name
        return DB.create_table(klass.table_name, query)

    def to_s(self):
        print (self.id, self.cache_dir_id, self.website_id, self.filename, self.size, self.access_time, self.access_count)
