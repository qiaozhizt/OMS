# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
import logging
import datetime
import time
from datetime import timedelta
from django.db import connections, transaction
from report.models import ReportConfig, ReportInfo, ReportInfoLine
from util.db_helper import namedtuplefetchall, dictfetchall

from django.http import HttpRequest
import pandas as pd
from StyleFrame import StyleFrame, Styler, utils
from dingtalk import SecretClient, AppKeyClient
from dingtalk.model import message
from urllib3 import encode_multipart_formdata
import requests
import simplejson as json

from util.db_helper import *
from util.dict_helper import *
from pg_oms import settings

from oms.models.order_models import LabOrder
from util.response import *


class ShippingOrdersReport:
    """
    Shipping Orders Report
    created by guof.
    2020.04.09
    """

    def get_summary_report(self, request, data):
        rm = response_message()
        overdue_days = data.get('overdue_days', 2)
        vendor = data.get('vendor', 'all')
        priority = data.get('priority', 'all')
        ship_direction = data.get('ship_direction', 'all')
        sql = '''
            /*
            每日统计各vd超期订单 汇总
            */
            select t0.id
            ,t0.order_number
            ,t0.lab_number
            ,t0.ship_direction
            ,t1.box_id
            ,t0.shipping_number
            ,t0.order_datetime as web_created_at
            ,t0.create_at as job_created_at
            ,t1.created_at as ship_created_at
            ,timestampdiff(day,t1.created_at,CURDATE()) as ship_days
            ,timestampdiff(hour,t0.create_at,t1.created_at) as diff_ship_hours
            ,timestampdiff(day,t0.create_at,t1.created_at) as diff_ship_days
            from oms_laborder t0
            left join shipment_glasses_box_item t1
            on t0.id=t1.lab_order_entity
            where date(t0.create_at)>=date_sub(now(),interval 3 month)
            and t0.status='SHIPPING'
            limit 30
            ;
        '''

        if vendor != 'all':
            ext_conditions = " and t0.vendor='%s'" % vendor
        else:
            ext_conditions = ' '

        if priority != 'all':
            ext_conditions += " and t0.priority='%s'" % priority

        if ship_direction != 'all':
            ext_conditions += " and t0.ship_direction='%s'" % ship_direction

        sql = sql % (ext_conditions, overdue_days)

        results = DbHelper.query(sql)

        rm.obj = results

        return rm

    def get_list_report(self, request, data):
        rm = response_message()
        lab_number = data.get('lab_number', '')
        box_id = data.get('box_id', 'all')
        ship_direction = data.get('ship_direction', 'all')
        sql = '''
            /*
            每日统计各vd超期订单 汇总
            */
            select t0.id
            ,t0.order_number
            ,t0.lab_number
            ,t0.ship_direction
            ,t1.pre_delivery_entity_id as box_id
            ,t0.shipping_number
            ,t0.tracking_code
            ,t0.order_datetime as web_created_at
            ,t0.create_at as job_created_at
            ,t1.created_at as ship_created_at
            ,timestampdiff(day,t1.created_at,CURDATE()) as ship_days
            ,timestampdiff(hour,t0.create_at,t1.created_at) as diff_ship_hours
            ,timestampdiff(day,t0.create_at,t1.created_at) as diff_ship_days
            from oms_laborder t0
            left join shipment_pre_delivery_line t1
            on t0.id=t1.lab_order_entity_id
            -- where date(t0.create_at)>=date_sub(now(),interval 3 month)
            where date(t0.create_at)>date('2020.01.01')
            and t0.status='SHIPPING'
            %s
            ;
        '''

        if lab_number:
            ext_conditions = " and t0.lab_number like '%%%s%%'" % lab_number
        else:
            ext_conditions = ' '

            if ship_direction != 'all':
                ext_conditions += " and t0.ship_direction='%s'" % ship_direction

            if box_id != 'all' and box_id != 'None':
                ext_conditions += " and t1.pre_delivery_entity_id=%s " % box_id
            elif box_id == 'None':
                ext_conditions += " and t1.pre_delivery_entity_id is null "

        sql = sql % ext_conditions

        data = DbHelper.query_with_titles(sql)

        res = {}
        res["items"] = data['results']
        res['sql_script'] = sql
        res['titles'] = data['titles']
        rm.obj = res

        return rm

    def get_box_id_list(self, request, parameters=None):
        rm = response_message()
        sql = '''
            /*
            每日统计各vd超期订单 汇总
            */
            select
            t1.pre_delivery_entity_id as box_id
            from oms_laborder t0
            left join shipment_pre_delivery_line t1
            on t0.id=t1.lab_order_entity_id
            where date(t0.create_at)>=date_sub(now(),interval 3 month)
            and t0.status='SHIPPING'
            group by t1.pre_delivery_entity_id;
        '''

        data = DbHelper.query_with_titles(sql)

        res = {}
        res["items"] = data['results']
        res['sql_script'] = sql
        res['titles'] = data['titles']
        rm.obj = res

        return rm

    def get_delivered_box_id_list(self, request, parameters=None):
        rm = response_message()
        sql = '''
            /*
            每日统计各vd超期订单 汇总
            */
            select
            distinct t1.pre_delivery_entity_id as box_id
            from oms_laborder t0
            left join shipment_pre_delivery_line t1
            on t0.id=t1.lab_order_entity_id
            where date(t0.create_at)>=date_sub(now(),interval 3 month)
            and t0.status='DELIVERED'
            order by t1.pre_delivery_entity_id;
        '''

        data = DbHelper.query_with_titles(sql)

        res = {}
        res["items"] = data['results']
        res['sql_script'] = sql
        res['titles'] = data['titles']
        rm.obj = res

        return rm

    def get_list_delivered_report(self, request, data):
        rm = response_message()
        lab_number = data.get('lab_number', '')
        box_id = data.get('box_id', 'all')
        ship_direction = data.get('ship_direction', 'all')
        time_type = data.get('time_type','all')
        start_date = data.get('start_date', '')
        end_date = data.get('end_date', '')

        sql = '''
            /*
            每日统计各vd超期订单 汇总
            */
            select t0.id
            ,t0.order_number
            ,t0.lab_number
            ,t0.ship_direction
            ,t1.pre_delivery_entity_id as box_id
            ,t0.shipping_number
            ,t0.tracking_code
            ,t0.order_datetime as web_created_at
            ,t0.create_at as job_created_at
            ,t1.created_at as ship_created_at
            ,date_add(t0.delivered_at,interval 8 hour) as delivered_at 
            ,TRUNCATE((timestampdiff(hour,t1.created_at,delivered_at))/24,1) as diff_delivered_days
            ,timestampdiff(day,t1.created_at,CURDATE()) as ship_days
            ,timestampdiff(hour,t0.create_at,t1.created_at) as diff_ship_hours
            ,TRUNCATE((timestampdiff(hour,t0.create_at,t1.created_at))/24,1) as diff_ship_days
            from oms_laborder t0
            left join shipment_pre_delivery_line t1
            on t0.id=t1.lab_order_entity_id
            where date(t0.create_at)>=date_sub(now(),interval 3 month)
            and date(t0.create_at)>date('2020.01.01')
            and t0.status='DELIVERED'
            %s
            ;
        '''

        if lab_number:
            ext_conditions = " and t0.lab_number like '%%%s%%'" % lab_number
        else:
            ext_conditions = ' '

            if ship_direction != 'all':
                ext_conditions += " and t0.ship_direction='%s'" % ship_direction

            if box_id != 'all' and box_id != 'None':
                ext_conditions += " and t1.pre_delivery_entity_id=%s " % box_id
            elif box_id == 'None':
                ext_conditions += " and t1.pre_delivery_entity_id is null "

            if time_type != 'all' and time_type != 'None':
                if time_type == 'web_time':
                    ext_conditions += " and t0.order_datetime between '{0}' and '{1}'".format(start_date,end_date)
                elif time_type == 'job_time':
                    ext_conditions += " and t0.create_at between '{0}' and '{1}'".format(start_date,end_date)
                elif time_type == 'ship_time':
                    ext_conditions += " and t1.created_at between '{0}' and '{1}'".format(start_date,end_date)
                elif time_type == 'due_time':
                    ext_conditions += " and delivered_at between '{0}' and '{1}'".format(start_date,end_date)


        sql = sql % ext_conditions

        data = DbHelper.query_with_titles(sql)

        res = {}
        res["items"] = data['results']
        res['sql_script'] = sql
        res['titles'] = data['titles']
        rm.obj = res

        return rm

    def get_delivered_avg_day(self, request, data):
        rm = response_message()
        box_id = data.get('box_id', 'all')

        sql = '''
            /*
                统计不同box_id的平均物流天数
            */
            select t1.pre_delivery_entity_id as box_id
            ,TRUNCATE(sum(timestampdiff(hour,t1.created_at,delivered_at))/24,1) as total_day
            ,count(timestampdiff(day,t1.created_at,delivered_at)) as count_day
            ,TRUNCATE(sum(timestampdiff(hour,t1.created_at,delivered_at))/24/count(*),1) as avg_day
            from oms_laborder t0
            left join shipment_pre_delivery_line t1
            on t0.id=t1.lab_order_entity_id
            where date(t0.create_at)>=date_sub(now(),interval 3 month)
            and date(t0.create_at)>date('2020.01.01')
            and t0.status='DELIVERED'
			%s;
        '''
        ext_conditions = ' '
        if box_id != 'all' and box_id != 'None':
            ext_conditions += " and t1.pre_delivery_entity_id=%s " % box_id
        elif box_id == 'None':
            ext_conditions += " and t1.pre_delivery_entity_id is null "

        sql = sql % ext_conditions

        data = DbHelper.query_with_titles(sql)

        res = {}
        res["items"] = data['results']
        res['sql_script'] = sql
        res['titles'] = data['titles']
        rm.obj = res

        return rm
