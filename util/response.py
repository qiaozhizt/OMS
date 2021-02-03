# -*- coding: utf-8 -*-


from django.db import connections
from django.db import transaction
from collections import namedtuple
from django.http import HttpResponse
import json

class response_message:
    def __init__(self):
        self.obj = None
        self.count = 0
        self.code = 0
        self.message = ''
        self.exception = None

    def capture_execption(self, e):
        self.code = -1
        self.message = 'Exception: %s' % str(e)
        self.exception = e.__dict__

    @staticmethod
    def response_dict(code='0', msg='success'):
        return {'code': code, 'message': msg}


def json_response(code, msg='', data=''):
    return HttpResponse(json.dumps({'code': code, 'msg': msg, 'data': data}))


def json_response_page(code, msg='', count=0, data=''):
    return HttpResponse(json.dumps({'code': code, 'msg': msg, 'count': count, 'data': data}))

class options_choice:
    key = ''
    value = ''

    def tuple2dict(self, ts):
        items = []
        for t in ts:
            oc = options_choice()
            oc.key = t[0]
            oc.value = t[1]
            items.append(oc)

        return items

class ResponseMessage:
    def __init__(self):
        self.obj = None
        self.count = 0
        self.code = 0
        self.message = ''
        self.exception = None

    def capture_execption(self, e):
        self.code = -1
        self.message = 'Exception: %s' % str(e)
        self.exception = e.__dict__

    @staticmethod
    def response_dict(code='0', msg='success'):
        return {'code': code, 'message': msg}


def is_contain_chinese(check_str):
    """
    判断字符串中是否包含中文
    :param check_str: {str} 需要检测的字符串
    :return: {bool} 包含返回True， 不包含返回False
    """
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False


class MyException(Exception):
    def __init__(self, code, msg, data=None):
        self.code = code
        self.message = msg
        self.data = data

    #def get_data(self):
    #    return {"code": self.code, "message": self.message, "data": self.data}