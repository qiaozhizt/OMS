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


class OverdueOrderReport:
    """
    Overdue Orders Report
    created by guof.
    2020.03.27
    """

    def get_overdue_orders_summary_report(self, request, data):
        rm = response_message()
        overdue_days = data.get('overdue_days', 2)
        vendor = data.get('vendor', 'all')
        priority = data.get('priority', 'all')
        ship_direction = data.get('ship_direction', 'all')
        sql = '''
            /*
            每日统计各vd超期订单 汇总
            */
            select t0.status
            ,(case when t0.status='' or t0.status is null then '01.新订单'
            when t0.status='REQUEST_NOTES' then '02.出库申请'
            when t0.status='FRAME_OUTBOUND' then '03.镜架出库'
            when t0.status='PRINT_DATE' then '04.单证打印'
            when t0.status='LENS_OUTBOUND' then '05.镜片出库'
            when t0.status='LENS_REGISTRATION' then '06.来片登记'
            when t0.status='LENS_RETURN' then '07.镜片退货'
            when t0.status='LENS_RECEIVE' then '08.镜片收货'
            when t0.status='ASSEMBLING' then '09.待装配'
            when t0.status='ASSEMBLLED' then '10.装配完成'
            when t0.status='GLASSES_RECEIVE' then '11.成镜收货'
            when t0.status='FINAL_INSPECTION' then '12.终检'
            when t0.status='FINAL_INSPECTION_YES' then '13.终检合格'
            when t0.status='FINAL_INSPECTION_NO' then '14.终检不合格'
            when t0.status='GLASSES_RETURN' then '15.成镜返工'
            when t0.status='COLLECTION' then '16.归集'
            when t0.status='PRE_DELIVERY' then '17.预发货'
            when t0.status='PICKING' then '18.已拣配'
            when t0.status='ORDER_MATCH' then '19.订单配对'
            when t0.status='BOXING' then '20.装箱'
            when t0.status='R2HOLD' then '21.申请暂停'
            when t0.status='R2CANCEL' then '22.申请取消'
            when t0.status='ONHOLD' then '23.暂停'
            when t0.status='CANCELLED' then '24.取消'
            when t0.status='REDO' then '25.重做'
            else t0.status
            end) as status_cn
            ,count(t0.id) as qty
            from oms_laborder t0
            left join oms_laborder_purchase_order_line t1 on t1.laborder_entity_id = t0.id
            where 1=1
            and date(t0.create_at)>=date('2019.01.01')
            and t0.status not in ('SHIPPING',
            -- 'R2HOLD',
            -- 'ONHOLD',
            'DELIVERED',
            'COMPLETE',
            'CLOSED',
            'R2CANCEL',
            'CANCELLED',
            'REDO',

            'PRE_DELIVERY',
            'PICKING',
            'BOXING'
            )

            %s

            and datediff(utc_date(),t0.order_datetime)>=%s
            -- and vendor='4'
            group by status_cn
            -- order by
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

    def get_overdue_orders_list_report(self, request, data):
        rm = response_message()
        lab_number = data.get('lab_number', '')
        overdue_days = data.get('overdue_days', 2)
        status = data.get('status', 'all')
        vendor = data.get('vendor', 'all')
        priority = data.get('priority', 'all')
        ship_direction = data.get('ship_direction', 'all')
        sql = '''
            /*
            每日统计各vd超期订单 清单
            */
            select t0.id
            ,t0.lab_number
            ,t0.priority
            ,t0.ship_direction
            ,(case when t0.ship_direction='STANDARD' then '普通'
            when t0.ship_direction='EXPRESS' then '加急'
            when t0.ship_direction='EMPLOYEE' then '内部员工'
            when t0.ship_direction='FLATRATE' then '批量'
            when t0.ship_direction='CA_EXPRESS' then '加拿大加急'
            when t0.ship_direction='US' then '美国'
            when t0.ship_direction='CN' then '国内小程序'
            when t0.ship_direction='SF' then '国内顺丰'
            else t0.ship_direction end) as ship_direction_cn
            ,t0.status
            ,(case when t0.status='' or t0.status is null then '01.新订单'
            when t0.status='REQUEST_NOTES' then '02.出库申请'
            when t0.status='FRAME_OUTBOUND' then '03.镜架出库'
            when t0.status='PRINT_DATE' then '04.单证打印'
            when t0.status='LENS_OUTBOUND' then '05.镜片出库'
            when t0.status='LENS_REGISTRATION' then '06.来片登记'
            when t0.status='LENS_RETURN' then '07.镜片退货'
            when t0.status='LENS_RECEIVE' then '08.镜片收货'
            when t0.status='ASSEMBLING' then '09.待装配'
            when t0.status='ASSEMBLLED' then '10.装配完成'
            when t0.status='GLASSES_RECEIVE' then '11.成镜收货'
            when t0.status='FINAL_INSPECTION' then '12.终检'
            when t0.status='FINAL_INSPECTION_YES' then '13.终检合格'
            when t0.status='FINAL_INSPECTION_NO' then '14.终检失败'
            when t0.status='GLASSES_RETURN' then '15.成镜返工'
            when t0.status='COLLECTION' then '16.归集'
            when t0.status='PRE_DELIVERY' then '17.预发货'
            when t0.status='PICKING' then '18.已拣配'
            when t0.status='ORDER_MATCH' then '19.订单配对'
            when t0.status='BOXING' then '20.装箱'
            when t0.status='R2HOLD' then '21.申请暂停'
            when t0.status='R2CANCEL' then '22.申请取消'
            when t0.status='ONHOLD' then '23.暂停'
            when t0.status='CANCELLED' then '24.取消'
            when t0.status='REDO' then '25.重做'
            else t0.status
            end) as status_cn
            ,t0.vendor_order_status_code
            ,t0.vendor_order_status_value
            ,t0.vendor_order_status_updated_at
            ,t0.frame
            ,t0.act_lens_name
            ,date(convert_tz(t0.order_datetime,@@session.time_zone,'+8:00')) as order_created_at
            ,date(convert_tz(t0.create_at,@@session.time_zone,'+8:00')) as job_created_at
            ,date(convert_tz(t1.created_at,@@session.time_zone,'+8:00')) as po_created_at
            ,DATE_FORMAT(convert_tz(utc_date(),@@session.time_zone,'+8:00'),'%%Y-%%m-%%d') as report_created_at
            ,datediff(utc_date(),t1.created_at) as diff
            ,datediff(utc_date(),t0.order_datetime) as diff_od
            ,t0.exclude_days
            ,t0.vendor
            ,t0.cur_progress
            ,t0.overdue_reasons
            from oms_laborder t0
            left join oms_laborder_purchase_order_line t1 on t1.laborder_entity_id = t0.id
            where 1=1
            and date(t0.create_at)>=date('2019.01.01')
            and t0.status not in ('SHIPPING',
            -- 'R2HOLD',
            -- 'ONHOLD',
            'DELIVERED',
            'COMPLETE',
            'CLOSED',
            'R2CANCEL',
            'CANCELLED',
            'REDO',

            'PRE_DELIVERY',
            'PICKING',
            'BOXING'
            )
            %s
            and datediff(utc_date(),t0.order_datetime)>=%s
            -- and vendor='4'
            order by diff_od desc
            ;

        '''

        if lab_number:
            ext_conditions = " and t0.lab_number like '%%%s%%'" % lab_number
        else:
            if status != 'all':
                ext_conditions = " and t0.status='%s'" % status
            else:
                ext_conditions = ' '

            if vendor != 'all':
                ext_conditions += " and t0.vendor='%s'" % vendor

            if priority != 'all':
                ext_conditions += " and t0.priority='%s'" % priority

            if ship_direction != 'all':
                ext_conditions += " and t0.ship_direction='%s'" % ship_direction

        sql = sql % (ext_conditions, overdue_days)

        data = DbHelper.query_with_titles(sql)

        res = {}
        res["items"] = data['results']
        res['sql_script'] = sql
        res['titles'] = data['titles']
        rm.obj = res

        return rm
