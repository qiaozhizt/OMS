# -*- coding: utf-8 -*-


from django.db import connections
from django.db import transaction
from collections import namedtuple


def namedtuplefetchall(cursor):
    "Return all rows from a cursor as a namedtuple"
    desc = cursor.description
    nt_result = namedtuple('Result', [col[0] for col in desc])
    return [nt_result(*row) for row in cursor.fetchall()]


def dictfetchall(cursor):
    "Return all rows from a cursor as a dict"
    columns = [col[0] for col in cursor.description]
    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


class SqlError(Exception):
    def __init__(self, funcname, sql, message=None):
        self.funcname = funcname
        self.sql = sql
        self.message = message

    def __str__(self):
        message = u"[%s]Error. %s" % (self.funcname, self.sql)
        if self.message:
            message += '[%s]' % self.message
        return message


def insert(cursor, sql, params=()):
    try:
        print(sql)
        cursor.execute(sql, params)
        return cursor.lastrowid
    except Exception as e:
        raise SqlError('insert', sql % params, e)
    finally:
        cursor.close()


def update(cursor, sql, params=()):
    try:
        cursor.execute(sql, params)
    except Exception as e:
        raise SqlError('update', sql % params, e)
    finally:
        cursor.close()


def delete(cursor, sql, params=()):
    try:
        cursor.execute(sql, params)
    except Exception as e:
        raise SqlError('delete', sql % params, e)
    finally:
        cursor.close()


def select(cursor, sql, params=()):
    try:
        cursor.execute(sql, params)
    except Exception as e:
        raise SqlError('delete', sql % params, e)


class DbHelper:
    @staticmethod
    def execute(sql, conn=None):
        if not conn:
            conn = connections['default']
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
        except Exception as ex:
            raise ex
        finally:
            conn.close()


    @staticmethod
    def query(sql, conn=None):
        results = None
        if not conn:
            conn = connections['pg_oms_query']
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)
        except Exception as ex:
            raise ex
        finally:
            conn.close()

        return results

    @staticmethod
    def query_with_titles(sql, conn=None):
        data = {}
        data_list = []
        if not conn:
            conn = connections['pg_oms_query']
        try:
            with conn.cursor() as cursor:
                cursor.execute(sql)

                for field in cursor.description:
                    data_list.append(field[0])

                results = namedtuplefetchall(cursor)
        except Exception as ex:
            raise ex
        finally:
            conn.close()

        data['titles'] = data_list
        data['results'] = results
        return data

    @staticmethod
    def get_titles(cursor_description):
        data_list = []
        for field in cursor_description:
            data_list.append(field[0])
        return data_list
