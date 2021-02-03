# -*- coding: utf-8 -*-
import datetime


def time_delta():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-90)
    return timedel


def time_delta_week():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-7)
    return timedel


def time_delta_month():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-30)
    return timedel

def time_delta_month_3():
    now_date = datetime.datetime.utcnow()
    timedel = now_date + datetime.timedelta(days=-90)
    return timedel

def days(day1, day2):
    num = (day2 - day1).days
    return num


def months(day1, day2):
    num = (day2.year - day1.year) * 12 + day2.month - day1.month
    return num


def dateDiffInHours(t1, t2):
    td = t2 - t1
    return td.days * 24 + td.seconds / 3600 + 1


def db_convert2bj(dtnow):
    nw = datetime.datetime.now()
    try:
        nw = dtnow + datetime.timedelta(hours=+8)
        return nw
    except Exception as ex:
        return nw

def bj_convet2db(dtnow):
    nw = datetime.datetime.now()
    try:
        nw = dtnow + datetime.timedelta(hours=-8)
        return nw
    except Exception as ex:
        return nw