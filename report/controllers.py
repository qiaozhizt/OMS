# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db.models import Q

from django.utils import timezone
# Create your models here.
from django.urls import reverse
import logging
from time import strftime
from django.db import connections
from django.db import transaction
from decimal import Decimal

from oms.models import OperationLog, PgOrderItem
from oms.models.ordertracking_models import OrderTracking
from shipment.models import pre_delivery_line
from util.db_helper import *

from oms.models.order_models import LabOrder, PgOrder
from util.time_delta import *
from util.base_type import base_type
from util.response import response_message
from const import *
from django.core import serializers
from util.dict_helper import dict_helper
import simplejson as json
from util.format_helper import *

from .models import *


class ReportJobStageController:
    def generate(self):
        try:
            logging.debug('start generate job stage report ....')

            # 2020.02.05 by guof. OMS-594
            # Job Type: RX_TINT
            sql = '''
                select
                utc_date() as u_date,
                utc_time() as u_time,
                date(convert_tz(utc_date(),@@session.time_zone,'+8:00')) as bj_date,
                time(convert_tz(utc_time(),@@session.time_zone,'+8:00')) as bj_time,
                year(date(convert_tz(utc_date(),@@session.time_zone,'+8:00'))) as year,
                month(date(convert_tz(utc_date(),@@session.time_zone,'+8:00'))) as month,
                day(date(convert_tz(utc_date(),@@session.time_zone,'+8:00'))) as day,
                hour(time(convert_tz(utc_time(),@@session.time_zone,'+8:00'))) as hour,
                'RX_TINT' as job_type,
                t0.status,
                case when t0.status='' then '新订单'
                when t0.status='REQUEST_NOTES' then '出库申请'
                when t0.status='LENS_OUTBOUND' then '镜架出库'
                when t0.status='PRINT_DATE' then '单证打印'
                when t0.status='LENS_REGISTRATION' then '来片登记'
                when t0.status='LENS_RECEIVE' then '镜片收货'
                when t0.status='COLLECTION' then '归集'
                when t0.status='ASSEMBLING' then '装配中'

                when t0.status='BOXING' then '装箱'
                when t0.status='FINAL_INSPECTION' then '终检'
                when t0.status='FINAL_INSPECTION_YES' then '终检合格'
                when t0.status='FRAME_OUTBOUND' then '镜架出库'
                when t0.status='GLASSES_RECEIVE' then '成镜收货'
                when t0.status='GLASSES_RETURN' then '成镜退货'
                when t0.status='LENS_RETURN' then '镜片退货'
                when t0.status='ORDER_MATCH' then '订单配对'
                when t0.status='PICKING' then '已拣配'
                when t0.status='PRE_DELIVERY' then '预发货'

                end as status_cn,

                case
                when t0.status in ('','REQUEST_NOTES','FRAME_OUTBOUND','PRINT_DATE','','','') then '1.外面在做的'
                when t0.status in ('LENS_REGISTRATION','LENS_RECEIVE','ASSEMBLING','ASSEMBLED','GLASSES_RECEIVE','FINAL_INSPECTION',
                'FINAL_INSPECTION_YES','COLLECTION') then '2.可以加工的'
                when t0.status in ('PRE_DELIVERY','PICKING','ORDER_MATCH','BOXING') then '3.加工完成未发货的'
                when t0.status in ('LENS_RETURN','FINAL_INSPECTION_NO','GLASSES_RETURN') then '4.我们准备的'
                else '未分类'
                end
                as stage,

                count(t0.id) as quantity from oms_laborder t0
                left join oms_labproduct lens
                on lens.sku = t0.lens_sku
                where 1=1
                and date(t0.create_at)>=date('2019.01.01')
                -- and lens.is_rx_lab=false
                and t0.vendor not in ('6','8','0','1000')
                and t0.status not in ('SHIPPING','DELIVERED','COMPLETE','CLOSED','CANCELLED','ONHOLD','R2HOLD','REDO','R2CANCEL')
                -- and t0.status in ('','PRINT_DATE','REQUEST_NOTES','LENS_OUTBOUND','ASSEMBLING','LENS_REGISTRATION','LENS_RECEIVE','COLLECTION')
                group by t0.status;
            '''

            with connections["default"].cursor() as cursor:
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)
                self.__set_values(results)

            # Job Type: STOCK
            sql = '''
            /* 统计可加工的订单-库存片订单 */
                select
                utc_date() as u_date,
                utc_time() as u_time,
                date(convert_tz(utc_date(),@@session.time_zone,'+8:00')) as bj_date,
                time(convert_tz(utc_time(),@@session.time_zone,'+8:00')) as bj_time,
                year(date(convert_tz(utc_date(),@@session.time_zone,'+8:00'))) as year,
                month(date(convert_tz(utc_date(),@@session.time_zone,'+8:00'))) as month,
                day(date(convert_tz(utc_date(),@@session.time_zone,'+8:00'))) as day,
                hour(time(convert_tz(utc_time(),@@session.time_zone,'+8:00'))) as hour,
                'STOCK' as job_type,
                t0.status,
                case when t0.status='' then '新订单'
                when t0.status='REQUEST_NOTES' then '出库申请'
                when t0.status='LENS_OUTBOUND' then '镜架出库'
                when t0.status='PRINT_DATE' then '单证打印'
                when t0.status='LENS_REGISTRATION' then '来片登记'
                when t0.status='LENS_RECEIVE' then '镜片收货'
                when t0.status='COLLECTION' then '归集'
                when t0.status='ASSEMBLING' then '装配中'

                when t0.status='BOXING' then '装箱'
                when t0.status='FINAL_INSPECTION' then '终检'
                when t0.status='FINAL_INSPECTION_YES' then '终检合格'
                when t0.status='FRAME_OUTBOUND' then '镜架出库'
                when t0.status='GLASSES_RECEIVE' then '成镜收货'
                when t0.status='GLASSES_RETURN' then '成镜退货'
                when t0.status='LENS_RETURN' then '镜片退货'
                when t0.status='ORDER_MATCH' then '订单配对'
                when t0.status='PICKING' then '已拣配'
                when t0.status='PRE_DELIVERY' then '预发货'

                end as status_cn,

                case
                when t0.status in ('','REQUEST_NOTES','FRAME_OUTBOUND','PRINT_DATE',
                'LENS_REGISTRATION','LENS_RECEIVE','ASSEMBLING','ASSEMBLED','GLASSES_RECEIVE','FINAL_INSPECTION',
                'FINAL_INSPECTION_YES','COLLECTION',
                'LENS_OUTBOUND') then '2.可以加工的'
                when t0.status in ('PRE_DELIVERY','PICKING','ORDER_MATCH','BOXING',
                'LENS_RETURN','FINAL_INSPECTION_NO','GLASSES_RETURN') then '3.加工完成未发货的'
                else '未分类'
                end
                as stage,

                count(t0.id) as quantity from oms_laborder t0
                left join oms_labproduct lens
                on lens.sku = t0.lens_sku
                where 1=1
                and date(t0.create_at)>=date('2019.01.01')
                -- and lens.is_rx_lab=false
                and t0.vendor in ('6','8')
                and t0.status not in ('SHIPPING','DELIVERED','COMPLETE','CLOSED','CANCELLED','ONHOLD','R2HOLD','REDO','R2CANCEL')
                -- and t0.status in ('','PRINT_DATE','REQUEST_NOTES','LENS_OUTBOUND','ASSEMBLING','LENS_REGISTRATION','LENS_RECEIVE','COLLECTION')
                group by t0.status;
            '''

            with connections["default"].cursor() as cursor:
                cursor.execute(sql)
                results = namedtuplefetchall(cursor)
                self.__set_values(results)

        except Exception as ex:
            logging.error(str(ex))


    def __set_values(self,results):
        for item in results:
            obj = ReportJobStage()
            obj.job_type = item.job_type
            obj.stage = item.stage
            obj.status = item.status
            obj.u_date = item.u_date
            obj.u_time = item.u_time
            obj.bj_date = item.bj_date
            obj.bj_time = item.bj_time
            obj.year = item.year
            obj.month = item.month
            obj.day = item.day
            obj.hour = item.hour
            obj.quantity = item.quantity

            obj.save()