# -*- coding: utf-8 -*-
import datetime
import time
import simplejson as json
import decimal

class format_date:
    @staticmethod
    def date2string(date):
        str_date = date.strftime("%Y-%m-%d")
        return str_date

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj,decimal.Decimal):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def dict_format(data_dict):
    try:
        for key in data_dict:
            if data_dict[key] is None:
                data_dict[key] = ''
        return data_dict
    except Exception as e:
        return data_dict


def str_format(data_str):
    try:
        if data_str is None:
            data_str = ''
        return data_str
    except Exception as e:
        return data_str

def get_datetime_by_en_str(t1):
    try:
        result = datetime.datetime.strptime(t1, '%B %d, %Y %I:%M %p')
        return result
    except Exception as ex:
        return ''