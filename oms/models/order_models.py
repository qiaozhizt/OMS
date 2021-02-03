# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from .dict_models import *
from .product_models import *

import time
import datetime
import logging

from django.utils import timezone
from django.core import serializers
from holiday_setting_models import HolidaySetting

from django.forms import ModelForm

from .base_type_models import BaseType, OrderBaseTypeExtends
from django.forms import widgets as Fwidgets
from django.forms import Form
from .application_models import *
from collections import namedtuple
from django.shortcuts import render
from django.db import connections
from django.db import transaction
from django.http import HttpResponse
from ..const import *
from django.db.models import Q
import json
from .post_models import *
import urllib2
from utilities_models import *
from pg_oms.settings import *
from pg_oms.settings import *
from utilities_models import *
from oms.const import *
from util.db_helper import *
from vendor.models import lens_order

from base_type_models import construction_voucher_base
from enum import Enum
from api.controllers.pgorder_frame_controllers import pgorder_frame_controller

from accsorder.models import AccsOrder
from accsorder.controller import AccsOrderController

class OrderActivity(models.Model):
    def __str__(self):
        return str(self.id) + ':' + self.type

    ACTIVITY_STATUS = (
        ('NEW', 'New'),
        ('PROCESSING', 'Processing'),
        ('COPMPLETE', 'Complete'),

    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OACT', editable=False)  # 操作日志

    object_type = models.CharField(u'Object Type', max_length=128, default='')
    object_entity = models.CharField(u'Object Entity', max_length=128, default='')
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True)
    action = models.CharField(u'Action', max_length=128, default='', null=True)

    user_entity = models.CharField(u'User Entity', max_length=128, default='', null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', null=True)

    comments = models.TextField(u'Comments', null=True, blank=True, default='')
    status = models.CharField(u'Status', max_length=128, null=True, blank=True, default="NEW", choices=ACTIVITY_STATUS)

    is_async = models.BooleanField(u'Is Async', default=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    is_send = models.BooleanField(u'Is Send', default=False)

    def query_by_id(self, id):
        oa = OrderActivity.objects.get(pk=id)
        return oa

    def query_by_type(self, type):
        queryset = OrderActivity.objects.filter(~Q(comments=None), ~Q(comments=''), object_type=type).order_by("-id")
        return queryset

    def add_activity(self, type, id, order_number, action_value, user_entity, user_name,
                     comments=None, status="NEW"
                     ):
        logging.debug("add_activity==>" + str(type))
        logging.debug("add_activity==>" + str(id))
        logging.debug("add_activity==>" + str(order_number))
        logging.debug("add_activity==>" + str(action_value))
        logging.debug("add_activity==>" + str(user_entity))
        logging.debug("add_activity==>" + str(user_name))
        logging.debug("add_activity==>" + str(comments))
        try:
            self.object_type = type
            self.object_entity = id
            self.order_number = order_number
            self.action = action_value

            self.user_entity = user_entity
            self.user_name = user_name

            self.comments = comments
            self.status = status

            self.save()
            return 'Success'
        except Exception as e:
            logging.error("Error==>" + str(e))
            return str(e)

    def change_activity(self, comments):
        self.comments = comments
        self.save()

    def change_status(self, status):
        self.status = status
        self.save()

    def queryActivities(self, order_number, obj_type):
        queryset = OrderActivity.objects.filter(order_number=order_number, object_type=obj_type).order_by('-id')
        results = serializers.serialize('json', queryset)
        return results

    # changeIs_Send
    def changeSendStatus(self):
        self.is_send = True
        self.save()


class LabOrder(OrderBaseTypeExtends):
    def __str__(self):
        return str(self.id) + ' : ' + self.lab_number

    '''距规定时间（小时）'''

    def set_time_calculate(self):
        now = timezone.now()

        if self.final_time <> '' and self.final_time <> None and self.targeted_date <> None:
            begin = self.final_time
            end = self.targeted_date
            if begin > end:
                begin = self.targeted_date
                end = self.final_time
            hs = HolidaySetting()
            us_holiday = hs.holiday(begin)
            poi = PgOrderItem()
            date_list = poi.inter_day(begin, end, us_holiday)

            logging.debug("final_time==>%s" % self.final_time)
            logging.debug("targeted_date==>%s" % self.targeted_date)
            hours = (time.mktime(self.targeted_date.timetuple()) - time.mktime(
                self.final_time.timetuple())) / 3600 - 24 * len(date_list)
        elif self.targeted_date <> None:
            begin = datetime.datetime.fromtimestamp(time.time())
            end = self.targeted_date
            begintime = int(time.time())
            endtime = int(time.mktime(self.targeted_date.timetuple()))
            if begintime > endtime:
                begin = self.targeted_date
                end = datetime.datetime.fromtimestamp(time.time())
            hs = HolidaySetting()
            us_holiday = hs.holiday(begin)
            poi = PgOrderItem()
            date_list = poi.inter_day(begin, end, us_holiday)

            hours = (time.mktime(self.targeted_date.timetuple()) - time.time()) / 3600 - 24 * len(date_list)
        else:
            hours = 0

        return round(hours, 1)

    def find_order_match(self):
        lab = LabOrder.objects.filter(status='ORDER_MATCH')
        return lab

    # 查找所有未发货订单
    def find_all_noship(self):
        lab = LabOrder.objects.filter(~Q(status='REDO'), ~Q(status='CANCELLED'), ~Q(status='ONHOLD'),
                                      ~Q(status='COMPLETE'), ~Q(status='SHIPPING'))
        return lab

    '''生产天数'''

    def production_days_calculate(self):

        if self.estimated_date <> '' and self.estimated_date <> None:
            hs = HolidaySetting()
            us_holiday = hs.holiday(self.create_at)
            poi = PgOrderItem()
            date_list = poi.inter_day(self.create_at, self.estimated_date, us_holiday)
            days = round(
                (time.mktime(self.estimated_date.timetuple()) - time.mktime(self.create_at.timetuple())) / 86400,
                1) - len(date_list)
        else:
            days = 0

        return round(days, 1)

    #  Type
    SHIP_DIRECTION_CHOICES = (
        ('STANDARD', '普通'),
        ('EXPRESS', '加急'),
        ('EMPLOYEE', '内部'),
        ('FLATRATE', '批量'),
        ('CA_EXPRESS','加急-加拿大'),
        ('US', '美国'),
        ('CN', '国内小程序'),
        ('SF', '国内顺丰'),
    )
    # 原垂直棱镜方向保留up&down 向下兼容
    BASE_CHOICES = (
        ('', ''),
        ('IN', 'In'),
        ('OUT', 'Out'),
        ('UP', 'Up(Deprecated)'),
        ('DOWN', 'Down(Deprecated)')
    )
    # 拓展垂直棱镜方向字段
    BASE_CHOICES_V = (
        ('', ''),
        ('UP', 'Up'),
        ('DOWN', 'Down')
    )
    PRESCRIPTION_CHOICES = (
        ('', 'NULL'),
        ('N', '平光'),
        ('S', '单光'),
        ('P', '渐进')
    )
    USED_FOR_CHOICES = (
        ('', 'NULL'),
        ('PROGRESSIVE', '渐进'),
        ('DISTANCE', '驾驶'),
        ('READING', '阅读')
    )

    STATUS_CHOICES = LAB_STATUS_CHOICES

    CHANGE_REASON_CHOICES = (
        ('OUT_STOCK', '无库存'),
        ('DIAMETER_LIMIT', '直径不足'),
        ('ADDITIONAL_WEIGHT', '度数差配重')
    )

    VENDOR_CHOICES = (
        ('0', '0'),
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
        ('6', '6'),
        ('7', '7'),
        ('8', '8'),
        ('9', '9'),
        ('10', '10'),
        ('11', '11'),
        ('12', '12'),
        ('13', '13'),
        ('14', '14'),
        ('15', '15'),
        ('1000', '1000-Frame Only'),
        ('1001', '1001-Stock Order')
    )

    WORKSHOP_CHOICES = (
        ('0', '0-未指定'),
        ('1', '1-怡华[停用]'),
        ('2', '2-薛斌[停用]'),
        ('3', '3-靖悦'),
        ('4', '4-三间下[停用]'),
        ('5', '5-上海伟星成镜'),
        ('6', '6-智镜上海分部'),
        ('8', '8-智镜本部'),
    )

    TIME_TYPE_CHOICES = (
        ('web_time','网上订单创建时间'),
        ('job_time','工厂订单创建时间'),
        ('ship_time','发货订单创建时间'),
        ('due_time','妥投订单创建时间'),
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OLOR', editable=False)  # 订单

    lab_number = models.CharField(u'单号', max_length=128, default='', null=True, unique=True)  # 该属性必须唯一
    status = models.CharField(u'状态', max_length=128, null=True, blank=True, default='', choices=STATUS_CHOICES)
    current_status = models.CharField(u'当前状态', max_length=128, null=True, blank=True, default='',
                                      choices=STATUS_CHOICES)

    # General
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True)
    # editable=False)

    chanel = models.CharField(u'Chanel', max_length=128, default='WEBSITE', null=True, editable=False)
    is_vip = models.BooleanField(u'VIP', default=False)

    ship_direction = models.CharField(u'配送方法', max_length=40, default='STANDARD',
                                      choices=SHIP_DIRECTION_CHOICES)

    act_ship_direction = models.CharField(u'实际配送方法', max_length=40, default='STANDARD',
                                          choices=SHIP_DIRECTION_CHOICES)

    base_entity = models.CharField(u'基础单据', max_length=128, default='', null=True)

    order_date = models.DateField(u'订单日期', null=True, blank=True)

    order_datetime = models.DateTimeField(u'订单日期', null=True, blank=True)

    comments = models.TextField(u'备注', max_length=512, default='', null=True, blank=True)

    pupils_position = models.IntegerField(u'Pupils Position', default=0)
    pupils_position_name = models.CharField(u'Pupils Position Name', max_length=255, default='', null=True, blank=True)

    user_id = models.CharField(u'ID', max_length=128, default='1', blank=True, null=True)
    user_name = models.CharField(u'用户名', max_length=128, default='SYSTEM', blank=True, null=True)

    # Lines
    frame = models.CharField(u'镜架编码', max_length=128, default='', null=True)
    name = models.CharField(u'镜架', max_length=512, default='', null=True, blank=True)
    size = models.CharField(u'大小', max_length=40, default='', null=True, blank=True)

    lens_width = models.IntegerField(u'框宽', default=0)
    bridge = models.IntegerField(u'桥', default=0)
    temple_length = models.IntegerField(u'腿长', default=0)

    lens_height = models.IntegerField(u'框高', default=0)

    quantity = models.IntegerField(u'数量', default=1)

    lens_sku = models.CharField(u'镜片编码', max_length=128, default='', null=True)
    lens_name = models.CharField(u'镜片', max_length=512, default='', null=True, blank=True)

    # 2018.02.21 by guof.
    act_lens_sku = models.CharField(u'实用镜片编码', max_length=128, default='', null=True, blank=True)
    act_lens_name = models.CharField(u'实用镜片', max_length=512, default='', null=True, blank=True)
    change_reason = models.CharField(u'变更原因', max_length=128, default='OUT_STOCK', null=True, blank=True,
                                     choices=CHANGE_REASON_CHOICES)
    lens_delivery_time = models.DateTimeField(u'镜片收货时间', null=True, blank=True)

    coating_sku = models.CharField(u'涂层编码', max_length=128, default='', null=True, blank=True)
    coating_name = models.CharField(u'涂层', max_length=512, default='', null=True, blank=True)

    tint_sku = models.CharField(u'染色编码', max_length=128, default='', null=True, blank=True)
    tint_name = models.CharField(u'染色', max_length=512, default='', null=True, blank=True)

    # Prescription
    profile_id = models.CharField(u'Profile ID', max_length=128, default='', null=True, blank=True)
    profile_name = models.CharField(u'Profile Name', max_length=255, default='', null=True,
                                    blank=True)
    profile_prescription_id = models.CharField(u'Profile Prescription ID', max_length=128, default='', null=True,
                                               blank=True)

    od_sph = models.DecimalField(u'光度(OD)', max_digits=5, decimal_places=2, default=0)
    od_cyl = models.DecimalField(u'散光(OD)', max_digits=5, decimal_places=2, default=0)
    od_axis = models.DecimalField(u'轴位(OD)', max_digits=5, decimal_places=0, default=0)
    os_sph = models.DecimalField(u'光度(OS)', max_digits=5, decimal_places=2, default=0)
    os_cyl = models.DecimalField(u'散光(OS)', max_digits=5, decimal_places=2, default=0)
    os_axis = models.DecimalField(u'轴位(OS)', max_digits=5, decimal_places=0, default=0)

    pd = models.DecimalField(u'瞳距', max_digits=5, decimal_places=1, default=0)
    is_singgle_pd = models.BooleanField(u'单眼瞳距', default=True)
    od_pd = models.DecimalField(u'瞳距(OD)', max_digits=5, decimal_places=1, default=0)
    os_pd = models.DecimalField(u'瞳距(OS)', max_digits=5, decimal_places=1, default=0)

    # Prescription extends

    od_add = models.DecimalField(u'渐进(OD)', max_digits=5, decimal_places=2, default=0)
    os_add = models.DecimalField(u'渐进(OS)', max_digits=5, decimal_places=2, default=0)

    od_prism = models.DecimalField(u'水平棱镜度(OD)', max_digits=5, decimal_places=2, default=0)
    od_base = models.CharField(u'水平棱镜方向(OD)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES)
    os_prism = models.DecimalField(u'水平棱镜度(OS)', max_digits=5, decimal_places=2, default=0)
    os_base = models.CharField(u'水平棱镜方向(OS)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES)

    # 拓展 垂直棱镜屈光度 和 垂直棱镜方向 (原 棱镜屈光度 和 棱镜方向)
    od_prism1 = models.DecimalField(u'垂直棱镜度(OD)', max_digits=5, decimal_places=2, default=0)
    od_base1 = models.CharField(u'垂直棱镜方向(OD)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES_V)
    os_prism1 = models.DecimalField(u'垂直棱镜度(OS)', max_digits=5, decimal_places=2, default=0)
    os_base1 = models.CharField(u'垂直棱镜方向(OS)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES_V)

    dia_1 = models.DecimalField(u'直径1', max_digits=10, decimal_places=2, default=0)
    dia_2 = models.DecimalField(u'直径2', max_digits=10, decimal_places=2, default=0)

    # jo-9
    prescription_id = models.CharField(u'验光单编码', max_length=40, null=True, blank=True, default='')
    prescription_name = models.CharField(u'验光单', max_length=128, null=True, blank=True, default='')
    prescription_type = models.CharField(u'验光单类型', max_length=128, null=True, blank=True, default='',
                                         choices=PRESCRIPTION_CHOICES)
    used_for = models.CharField(u'用途', max_length=40, null=True, blank=True, default='', choices=USED_FOR_CHOICES)

    # add lee 2018.8.21 添加progressive_type字段
    progressive_type = models.CharField(u'渐进类型', max_length=128, null=True, blank=True)

    # ordertracking->laborder

    estimated_ship_date = models.DateTimeField(u'预计发货时间', null=True, blank=True)
    final_time = models.DateTimeField(u'实际发货时间', null=True, blank=True, editable=False)
    carriers = models.CharField(u'承运商', max_length=128, null=True, blank=True, default='')
    shipping_number = models.CharField(u'运单号', max_length=128, null=True, blank=True, default='')
    tracking_code = models.CharField(u'Tracking Code', max_length=128, null=True, blank=True, default='')
    estimated_time = models.DateField(u'预计发货时间', null=True, blank=True)
    estimated_date = models.DateTimeField(u'预计完成时间', null=True, blank=True)
    targeted_date = models.DateTimeField(u'规定完成时间', null=True, blank=True)
    promised_date = models.DateTimeField(u'承诺完成时间', null=True, blank=True)
    set_time_1 = models.DecimalField(u'距规定时间', max_digits=5, decimal_places=1, default=0)
    production_days_1 = models.DecimalField(u'生产天数', max_digits=5, decimal_places=1, default=0)
    # production_days=self.production_days_calculate()

    qty_ordered = models.IntegerField(u'订单数量', default=0)

    # 2018.02.21 by guof.
    has_remake_orders = models.BooleanField(u'包含重做订单', default=False)
    is_remake_order = models.BooleanField(u'重做订单', default=False)
    is_glasses_return = models.BooleanField(u'成镜退货', default=False)
    qr_path = models.ImageField(upload_to='scan', null=True, blank=True)
    c39_path = models.ImageField(upload_to='scan', null=True, blank=True)
    c128_path = models.ImageField(upload_to='scan', null=True, blank=True)

    vendor = models.CharField(u'VD', max_length=128, null=True, blank=True, default='0', choices=VENDOR_CHOICES)
    workshop = models.CharField(u'Work Shop', max_length=128, null=True, blank=True, default='0',
                                choices=WORKSHOP_CHOICES)

    hours_of_purchase = models.IntegerField(u'Hours of Purchase', default=0)
    level_of_purchase = models.IntegerField(u'Level of Purchase', default=0)

    is_ai_checked = models.BooleanField(u'自动程序已检查', default=False)
    is_lens_order_created = models.BooleanField(u'Lens Order已创建', default=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

    vendor_order_reference = models.CharField(u'工厂订单号', max_length=128, default='', blank=True)
    vendor_order_status_code = models.CharField(u'Status Code', max_length=36, default='', null=True, blank=True)
    vendor_order_status_value = models.CharField(u'Status Value', max_length=20, default='', null=True, blank=True)
    vendor_order_status_updated_at = models.CharField(u'Updated At', max_length=36, default='', null=True, blank=True)

    image = models.CharField(u'Image', max_length=1024, default='', null=True, blank=True)
    thumbnail = models.CharField(u'Thumbnail', max_length=1024, default='', null=True, blank=True)
    category_id = models.CharField(u'Category id', null=True, max_length=128, default='', blank=True)
    tracking_number = models.CharField(u'Tracking Number', max_length=1024, default='', blank=True, null=True)
    overdue_reasons = models.TextField(u'超期原因', max_length=512, default='', null=True, blank=True)
    cur_progress = models.CharField(u'目前进度', max_length=1024, default='', null=True, blank=True)
    is_generated_production_report = models.BooleanField(u'Is Generated Production Report', default=False)
    is_production_change = models.BooleanField(u'Is Production Change', default=False)
    locker_number= models.CharField(u'Locker Number', max_length=128, default='', blank=True, null=True)  # 仓位编号
    exclude_days = models.CharField(u'Exclude Days', max_length=128, default='0', null=True, blank=True)
    exclude_time = models.CharField(u'Exclude Time', null=True, max_length=128, default='0', blank=True)
    weight = models.DecimalField(u'Weight', max_digits=5, decimal_places=2, default=0)
    weight_create_at = models.DateTimeField(null=True)
    operator_id = models.IntegerField(u'Weight Operator ID', default=0)
    operator_name = models.CharField(u'Weight Operator Name', max_length=128, default='', blank=True)
    gross_weight = models.DecimalField(u'Gross Weight', max_digits=5, decimal_places=2, default=0)
    is_push = models.BooleanField(u'Is Push', default=False)

    @property
    def get_bar_code(self):
        bar_code = '%s%d'
        bar_code = bar_code % (settings.BAR_CODE_PREFIX, self.id)
        return bar_code

    @property
    def get_reg_times(self):
        from qc.models import lens_registration
        lrs = lens_registration.objects.filter(laborder_entity=self)
        return lrs.count()

    @property
    def get_reg_glasses_times(self):
        from oms.models.glasses_models import received_glasses
        rgs = received_glasses.objects.filter(lab_order_entity=self.id)
        return rgs.count()

    @property
    def order_state(self):
        poi = PgOrderItem.objects.get(id=self.base_entity)
        return poi.pg_order_entity.region

    @property
    def order_ship_region(self):
        poi = PgOrderItem.objects.get(id=self.base_entity)
        return poi.pg_order_entity.ship_region

    def query_by_id(self, lab_number):
        laborder = LabOrder.objects.get(lab_number=lab_number)
        return laborder

    def filter_by_id(self, lab_number):
        laborderlist = LabOrder.objects.filter(lab_number__contains=lab_number)
        return laborderlist

    def modify_status(self, pk, action_value):
        los = LabOrder.objects.filter(base_entity=pk)
        for lo in los:
            if action_value == 'CANCELLED':

                lo.status = action_value
                lo.is_enabled = False
                lo.save()
            else:
                lo.status = action_value
                lo.save()
        return lo

    @property
    def lens_type(self):
        lens_sku = self.lens_sku
        try:
            lp = LabProduct.objects.get(sku=lens_sku)
            if lp.is_rx_lab:
                return 'C'
            else:
                return 'K'
        except:
            return 'N'

    @property
    def lens_index(self):
        lens_sku = self.lens_sku
        try:
            lp = LabProduct.objects.get(sku=lens_sku)
            return lp.index
        except:
            return 0

    @property
    def is_cyl_high(self):
        os_cyl = abs(self.os_cyl)
        od_cyl = abs(self.od_cyl)
        if od_cyl > 2 or os_cyl > 2:
            return True
        else:
            return False

    @property
    def days_of_production_by_order(self):
        try:
            return (timezone.now() - self.order_datetime).days
        except:
            return -1

    @property
    def days_of_production(self):
        try:
            return (timezone.now() - self.create_at).days
        except:
            return -1

    @property
    def days_of_lens_registration(self):
        try:
            from qc.models import lens_registration
            lrs = lens_registration.objects.filter(lab_number=self.lab_number).order_by('-id')[:1]

            from oms.models.glasses_models import received_glasses
            rgs = received_glasses.objects.filter(lab_number=self.lab_number).order_by('-id')[:1]

            if len(lrs) > 0:
                lr = lrs[0]
                return (lr.created_at - self.create_at).days
            elif len(rgs) > 0:
                rg = rgs[0]
                return (rg.created_at - self.create_at).days
            elif self.status == 'LENS_REGISTRATION' \
                    or self.status == 'ASSEMBLED' \
                    or self.status == 'GLASSES_RECEIVE' \
                    or self.status == 'FINAL_INSPECTION' \
                    or self.status == 'PICKING' \
                    or self.status == 'ORDER_MATCH' \
                    or self.status == 'SHIPPING' \
                    :
                return (timezone.now() - self.create_at).days
            else:
                return -2
        except:
            return -1

    @property
    def get_lens_registration_date(self):
        try:
            from qc.models import lens_registration
            lrs = lens_registration.objects.filter(lab_number=self.lab_number).order_by('-id')[:1]

            from oms.models.glasses_models import received_glasses
            rgs = received_glasses.objects.filter(lab_number=self.lab_number).order_by('-id')[:1]

            if len(lrs) > 0:
                lr = lrs[0]
                return lr.created_at
            elif len(rgs) > 0:
                rg = rgs[0]
                return rg.created_at
            else:
                return self.create_at
        except:
            return -1

    @property
    def is_procured(self):
        try:
            laborder_purchase_order_line.objects.get(laborder_entity=self)
            return True
        except:
            return False

    @property
    def get_box_id(self):
        try:
            # if self.ship_direction <> 'STANDARD':
            #     return '非普通发货无BOX'
            from shipment.models import pre_delivery_line
            pdls = pre_delivery_line.objects.filter(lab_order_entity=self)
            if pdls.count() > 0:
                pdl = pdls[0]
                return pdl.pre_delivery_entity.id

            return 0
        except:
            return -1

    @property
    def get_bag_id(self):
        try:
            # if self.ship_direction <> 'STANDARD':
            #     return '非普通发货无BOX'
            from shipment.models import glasses_box_item
            gbis = glasses_box_item.objects.filter(lab_number=self.lab_number)
            if gbis.count() > 0:
                gbi = gbis[0]
                return gbi.bag_id
            return 0
        except:
            return -1

    @property
    def get_can_ship(self):
        if self.status in ('PRE_DELIVERY', 'PICKING', 'ORDER_MATCH'):
            return True
        else:
            return False

    @property
    def get_days_of_purchase(self):
        try:
            from util import time_delta
            olpol = laborder_purchase_order_line.objects.get(lab_number=self.lab_number)
            return time_delta.dateDiffInHours(self.create_at, olpol.created_at)
            # return (timezone.now() - olpol.created_at).days
        except Exception as e:
            logging.debug(e.message)
            return time_delta.dateDiffInHours(self.create_at, timezone.now())
            # return (timezone.now() - self.create_at).days

    @property
    def get_purchase_date(self):
        try:
            olpol = laborder_purchase_order_line.objects.get(lab_number=self.lab_number)
            return olpol.created_at
            # return (timezone.now() - olpol.created_at).days
        except Exception as e:
            logging.debug(e.message)
            return self.create_at
            # return (timezone.now() - self.create_at).days

    # 获取出库申请单ID，没有返回空字符串
    @property
    def get_laborder_request_notes_id(self):
        lpo = laborder_request_notes_line.objects.filter(lab_number=self.lab_number)
        if lpo.count() < 1:
            return ''
        else:
            return lpo[0].lrn_id

    # 获取采购订单清单单ID，没有返回空字符串
    @property
    def get_laborder_purchase_order_id(self):
        lpo = laborder_purchase_order_line.objects.filter(lab_number=self.lab_number)
        if lpo.count() < 1:
            return ''
        else:
            return lpo[0].lpo_id

    # 获取成镜收货记录ID，没有返回空字符串
    @property
    def get_received_glasses_id(self):
        from oms.models.glasses_models import received_glasses
        rgs = received_glasses.objects.filter(lab_number=self.lab_number)
        if rgs.count() < 1:
            return ''
        else:
            return rgs[0].id

    @property
    def get_mono_pd_off_ctr_mm(self):  # 框心距与瞳距差值
        pd = self.pd
        if not self.is_singgle_pd:
            pd = self.od_pd + self.os_pd

        return self.lens_width + self.bridge - pd

'''
    # ('PURGING', '清洗'),
        ('PRE_DELIVERY', '预发货'),
        ('PICKING', '已拣配'),

        ('ORDER_MATCH', '订单配对'),
'''


class LabOrderForm(ModelForm):
    class Meta:
        model = LabOrder
        # fields = "__all__"
        fields = ['lab_number', 'base_entity', 'order_number', 'order_date', 'size', 'quantity', 'vendor',
                  'frame', 'name', 'lens_sku', 'lens_name', 'act_lens_sku', 'act_lens_name',
                  'coating_sku', 'coating_name', 'tint_sku', 'tint_name', 'od_sph', 'od_cyl', 'od_axis',
                  'is_singgle_pd', 'od_pd', 'od_add', 'od_prism', 'od_base', 'os_sph', 'os_cyl', 'os_axis',
                  'pd', 'os_pd', 'os_add', 'os_prism', 'os_base', 'comments', 'user_id', 'user_name', 'status',
                  'estimated_date', 'targeted_date', 'pal_design_name', 'profile_id', 'profile_name',
                  'prescription_id', 'prescription_name', 'prescription_type', 'used_for', 'act_ship_direction',
                  'estimated_time', 'promised_date', 'change_reason', 'estimated_date', 'estimated_ship_date',
                  'order_datetime', 'production_days_1', 'set_time_1', 'dia_1', 'dia_2', 'pupils_position',
                  'pupils_position_name', 'profile_prescription_id', 'asmbl_seght', 'lens_height', 'lens_seght',
                  'comments_inner', 'comments_ship', 'pal_design_sku', 'progressive_type', 'color', 'frame_type',
                  'lens_width', 'temple_length', 'bridge', 'lab_seg_height', 'assemble_height', 'sub_mirrors_height',
                  'special_handling', 'channel', 'os_prism1', 'os_base1', 'od_prism1', 'od_base1', 'image', 'thumbnail','category_id']
        widgets = {
            'comments': Fwidgets.Textarea(attrs={'required': True, 'rows': 3, 'cols': 50}),
            'comments_inner': Fwidgets.Textarea(attrs={'rows': 3, 'cols': 50})}


class LabOrder_QualityControl(BaseType):
    type = models.CharField(u'类型', max_length=20, default='LOQC', editable=False)
    laborder_entity = models.ForeignKey(LabOrder, models.SET_NULL,
                                        blank=True,
                                        null=True, )
    comments = models.TextField(u'Comments', max_length=4000, default='', null=True, blank=True)

    def add_object(self, laborder_entity, comments):
        loqc = LabOrder_QualityControl()
        loqc.laborder_entity = laborder_entity
        loqc.comments = comments
        loqc.save()


class PgOrder(models.Model):
    def __str__(self):
        return str(self.id) + ' : ' + self.order_number

    #  Type
    SHIP_DIRECTION_CHOICES = (
        ('STANDARD', 'Standard'),
        ('EXPRESS', 'Express'),
        ('EMPLOYEE', 'Employee'),
        ('FLATRATE', 'Flatrate'),
        ('CA_EXPRESS', 'Canda_Express'),
    )

    STATUS_CHOICES = PG_ORDER_STATUS_CHOICES
    INNER_LAB_STATUS_CHOICES = LAB_STATUS_CHOICES_EN

    STATUS_CONTROL_CHOICES = (
        ('', ''),
        ('REVIEWED', 'Reviewed'),
        ('APPROVED', 'Approved'),
        ('INLAB', 'In Lab'),
        ('SHIPPED', 'Shipped'),
        ('AI', 'Ai'),
        ('MANUAL', 'Manual')
    )

    STATUS_ADDRESS_CHOICES = (
        ('', ''),
        (0, ''),
        (1, 'Verified'),
        (2, 'Suggest'),
        (3, 'Any Way')
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OPOR', editable=False)  # 订单

    # General
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True,
                                    unique=True)  # , unique=True)  # 该属性必须唯一

    priority = models.IntegerField(u'Priority', default=4)

    origin_order_entity = models.CharField(u'Origin Order Entity', max_length=128, default='', null=True, blank=True)
    origin_order_number = models.CharField(u'Origin Order Number', max_length=128, default='', null=True, blank=True)
    is_remake_order = models.BooleanField(u'IS Remake Order', default=False)

    status = models.CharField(u'Status', max_length=128, default='', null=True, choices=STATUS_CHOICES)

    status_control = models.CharField(u'Status Control', max_length=128, default='', null=True, blank=True,
                                      choices=STATUS_CONTROL_CHOICES)

    lab_status = models.CharField(u'Lab Status', max_length=128, null=True, blank=True, default='',
                                  choices=LAB_STATUS_CHOICES_EN)

    web_status = models.CharField(u'Web Status', max_length=128, default='', null=True, choices=STATUS_CHOICES,
                                  editable=False)

    chanel = models.CharField(u'Chanel', max_length=128, default='WEBSITE', null=True ,blank=True)
    tag = models.CharField(u'Tag', max_length=128, default='WEBSITE', null=True, blank=True)

    is_vip = models.BooleanField(u'Is VIP', default=False)
    ship_direction = models.CharField(u'Ship Direction', max_length=40, default='STANDARD',
                                      choices=SHIP_DIRECTION_CHOICES)
    customer_id = models.CharField(u'Customer Entity', max_length=128, default='', null=True)

    billing_address_id = models.CharField(u'Billing Address Id', max_length=128, default='', null=True)
    shipping_address_id = models.CharField(u'Shipping Address Id', max_length=128, default='', null=True)

    base_entity = models.CharField(u'Base Entity', max_length=128, default='', null=True, blank=True)
    order_create_at = models.DateTimeField(null=True, blank=True, editable=False)
    order_date = models.DateField(null=True, blank=True)

    order_datetime = models.DateTimeField(null=True, blank=True)

    subtotal = models.DecimalField(u'Subtotal', max_digits=10, decimal_places=2, default=0)
    grand_total = models.DecimalField(u'Grand Total', max_digits=10, decimal_places=2, default=0)
    total_paid = models.DecimalField(u'Total Paid', max_digits=10, decimal_places=2, default=0)
    shipping_and_handling = models.DecimalField(u'Shipping And Handling', max_digits=10, decimal_places=2, default=0)
    base_discount_amount_order = models.DecimalField(u'Base Discount Amount Order', max_digits=10, decimal_places=2,
                                                     default=0)
    total_qty_ordered = models.DecimalField(u'Total Qty Ordered', max_digits=10, decimal_places=2, default=0)

    coupon_code = models.CharField(u'Coupon Code', max_length=255, default='', null=True, blank=True)
    coupon_rule_name = models.CharField(u'Coupon Rule Name', max_length=255, default='', null=True, blank=True)

    # 联系电话，联系邮件，添加日期  2018-08-29 ranhy
    relation_email = models.CharField(u'Contact Email', max_length=128, default='', null=True, blank=True)
    relation_phone = models.CharField(u'Contact Phone', max_length=128, default='', null=True, blank=True)
    relation_checked = models.BooleanField(u'Is Sync', default=False)
    relation_add_date = models.DateTimeField(u'Add Date', null=True, blank=True, editable=False)

    #Warranty add by ranhy 2019-9-2
    warranty = models.DecimalField(u'Warranty', max_digits=12, decimal_places=4, default=0,null=True, blank=True)
    row_total_without_warranty = models.DecimalField(u'Row Total Without Warranty', max_digits=12, decimal_places=4, default=0,null=True, blank=True)
    has_warranty = models.BooleanField(u'Has Warranty',default=False)

    street2 = models.CharField(u'Street2', max_length=512, default='', null=True, blank=True)
    address_verify_status = models.IntegerField(u'Verify Address Status', default=0,
                                                choices=STATUS_ADDRESS_CHOICES)

    # Shipping & Billing
    customer_name = models.CharField(u'Customer Name', max_length=128, default='', null=True)
    firstname = models.CharField(u'Firstname', max_length=128, default="", null=True)
    lastname = models.CharField(u'Lastname', max_length=128, default='', null=True)
    postcode = models.CharField(u'Postcode', max_length=10, default='', null=True)
    phone = models.CharField(u'Customer Phone', max_length=128, default='', null=True)
    street = models.CharField(u'Street', max_length=512, default='', null=True)
    city = models.CharField(u'City', max_length=128, default='', null=True)
    region = models.CharField(u'Region', max_length=128, default='', null=True)

    # west region before 2018.10
    # states_list = ['Arizona',
    #                'Alaska',
    #                'Colorado',
    #                'Oregon',
    #                'Montana',
    #                'Idaho',
    #                'Wyoming',
    #                'Nevada',
    #                'Utah',
    #                'New Mexico',
    #                'Washington',
    #                'California',
    #                # 'Texas',
    #                # 'Kansas',
    #                # 'Oklahoma',
    #                'Hawaii',
    #                # 'North Dakota',
    #                # 'South Dakota',
    #                # 'Nebraska',
    #                # 'Louisiana',
    #                # 'Puerto Rico',
    #                ]

    # web region 2018.10.04
    # 2019.04.04 guof.
    # 暂时停用东西部的区分
    # states_list = ['Arizona',
    #                'Alaska',
    #                'Colorado',
    #                'Oregon',
    #                'Montana',
    #                'Idaho',
    #                'Wyoming',
    #                'Nevada',
    #                'Utah',
    #                'New Mexico',
    #                'Washington',
    #                'California',
    #
    #                'Kansas',
    #                'Oklahoma',
    #                'Louisiana',
    #                'Nebraska',
    #                'North Dakota',
    #                'South Dakota',
    #                'Alaska',
    #                'Hawaii',
    #                'Texas',
    #                ]

    states_list = []

    @property
    def ship_region(self):
        if self.ship_direction == 'STANDARD':
            if self.region in self.states_list:
                return 'W'
            else:
                return 'E'
        else:
            return self.get_ship_direction_display()

    @property
    def get_thumbnail(self):
        try:
            pgoi = PgOrderItem.objects.get(id=self.base_entity)
            return pgoi.thumbnail
        except Exception as e:
            return None

    country_id = models.CharField(u'Country Id', max_length=128, default='', null=True)
    email = models.CharField(u'Customer Email', max_length=128, default='', null=True, blank=True)

    shipping_method = models.CharField(u'Shipping Method', max_length=128, null=False, blank=False, default='')
    shipping_description = models.CharField(u'Shipping Description', max_length=40, null=True, blank=True, default='')

    estimated_ship_date = models.DateTimeField(u'Est Ship Date', null=True, blank=True)
    estimated_date = models.DateTimeField(u'Est Date', null=True, blank=True)
    final_date = models.DateTimeField(u'Act Ship Date', null=True, blank=True)
    targeted_ship_date = models.DateTimeField(u'Targeted Ship Date', null=True, blank=True)
    promised_ship_date = models.DateTimeField(u'Promised Ship Date', null=True, blank=True)

    is_inlab = models.BooleanField(u'Is InLab', default=False)
    is_shiped_api = models.BooleanField(u'API', default=False)
    is_issue_addr = models.BooleanField(u'Is Issue Address', default=False)
    is_verified_addr = models.BooleanField(u'Is Verified Address', default=False)
    web_created_at = models.DateTimeField(u'Web Created At', null=True, blank=True, editable=False)
    web_updated_at = models.DateTimeField(u'Web Updated At', null=True, blank=True, editable=False)

    is_required_return_lable = models.BooleanField(u'Return Lable', default=False)

    is_inst = models.BooleanField(u'Has Instruction', default=False)
    instruction = models.TextField(u'Instruction', null=True, blank=True, default='')

    comments = models.TextField(u'Comments', default='', null=True, blank=True)
    # add by ranhy 2019-08-02
    send_invoic_info = models.TextField(u'Invoic Info', default='', null=False, blank=True)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

    delivered_at = models.DateTimeField(u'DELIVERED AT', null=True, blank=True)

    # 重做单的PG_order订单号
    reorder_number = models.CharField(u'ReOrder Number', max_length=128, default='', null=True, blank=True)

    is_generated_report_efficiency = models.BooleanField(u'Is Generated Report Efficiency', default=False)

    @property
    def has_reorder(self):
        if self.reorder_number == '' or self.reorder_number == None:
            return False
        return True

    @property
    def get_items(self):
        try:
            pgis = PgOrderItem.objects.filter(order_number=self.order_number)
            return pgis
        except Exception as e:
            return None

    def get_item(self, item_id):
        try:
            pgi = PgOrderItem.objects.filter(order_number=self.order_number, id=item_id)[0]
            return pgi
        except Exception as e:
            return None

    @property
    def get_lab_status(self):
        try:
            pgis = PgOrderItem.objects.filter(order_number=self.order_number)
            ls = []
            for pgi in pgis:
                if pgi.lab_order_entity:
                    ls.append(pgi.lab_order_entity.get_status_display())

            str_ls = ','.join(ls)
            return str_ls
        except Exception as e:
            return None

    @property
    def get_shipping_method(self):
        if self.shipping_method == 'standard_standard':
            return 'Standard'
        if self.shipping_method == 'express_express':
            return 'Express'
        if self.shipping_method == 'canada_express_canada_express':
            return 'CA_Express'
        return self.shipping_method

    """pgorder总条数"""

    def pgorder_count(self):
        count = PgOrder.objects.count()
        return count

    """查询某一页的数据"""

    def pgOrderList(self, currPage):
        curr = int(currPage)
        begin = (curr - 1) * 20
        if begin == 0:
            begin = None
            end = 20
        else:
            end = begin + 20
        logging.debug("begin==>" + str(begin))
        logging.debug("end==>" + str(end))

        # 2018.02.20 by guof
        # 增加 is_enabled = True 的限制

        queryset = PgOrder.objects.all().filter(is_enabled=True).order_by("-id")[begin:end]
        results = serializers.serialize('json', queryset)
        return results

    """生成laborder"""

    def generate_lab_orders(self):
        date_list = []
        pgois = PgOrderItem.objects.filter(pg_order_entity=self)
        logging.debug("================%s" % pgois)

        r_value = -1

        for pgoi in pgois:
            # 如果瞳高为空，为订单计算瞳高
            if (pgoi.lab_seg_height == '' or pgoi.lab_seg_height is None) and 'Bifocal' not in pgoi.lens_name:
                pgoi.lab_seg_height = str(0.5 * float(pgoi.lens_height) + 4)
                pgoi.assemble_height = 'STD+1.0'
                #20200811
                #pgoi.comments += '加工瞳高%smm;' % str(0.5 * float(pgoi.lens_height) + 4)
                pgoi.save()
            r_value = pgoi.generate_lab_orders()
            if pgoi.lab_order_entity:
                date_list.append(pgoi.lab_order_entity.targeted_date)

        if r_value == 0:
            self.is_inlab = True
            self.save()
        else:
            # logging.error("Lab Order has been generated!")
            raise ValueError, "Lab Order maybe has been generated!"

        return date_list

    """通过order_number查找object"""

    def query_by_id(self, order_number):
        pgorder = PgOrder.objects.get(order_number=order_number)

        return pgorder

    """修改pgorder的状态"""

    def modify_status(self, order_number, content, new_value, user):
        po = PgOrder.objects.get(order_number=order_number)
        ol = OperationLog()
        # new_value = action_value.lower()
        ol.log(po.type, po.id, content, "status", user, po.status, new_value)
        # status = action_value.lower()

        po.status = new_value
        po.save()

    def modify_spe_status(self, status):
        self.status = status
        self.save()


class PgOrderFormDetail(ModelForm):
    class Meta:
        model = PgOrder
        fields = ('order_number', 'customer_id','email','phone','priority',
                  'relation_email', 'relation_phone', 'order_datetime', 'status', 'status_control',
                  'estimated_ship_date', 'is_inst', 'instruction',
                  'final_date', 'targeted_ship_date',
                  'promised_ship_date', 'shipping_method',
                  'ship_direction', 'comments', 'is_inlab', 'is_shiped_api',
                  'coupon_code', 'coupon_rule_name', 'reorder_number','origin_order_number','has_warranty','warranty','tag')
        widgets = {'comments': Fwidgets.Textarea(attrs={'rows': 5, 'cols': 40})}
        # fields='__all__'


class CustomerAccountLog(models.Model):
    class Meta:
        db_table = 'customer_account_log'

    is_pwd = models.BooleanField(u'Is Change Password', default=False)
    customer_email = models.CharField(u'Customer Email', max_length=128, default='', null=True, blank=True)
    old_customer_email = models.CharField(u'Old Customer Email', max_length=128, default='', null=True, blank=True)
    user_entity = models.ForeignKey(User, models.SET_NULL,
                                    blank=True,
                                    null=True, )
    comments = models.CharField(u'Comments', max_length=512, default='', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


#重做单信息ranhy
class RemakeOrder(models.Model):
        class Meta:
            db_table = 'pg_order_remake'
        order_number = models.CharField(u'Order Number', max_length=128, default='', blank=True, null=True)
        item_id = models.CharField(u'Items ID', max_length=256, default='', null=True, blank=True)
        remake_order = models.CharField(u'Remake Order', max_length=256, default='', null=True, blank=True)
        user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True, editable=False)
        user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True, editable=False)
        comments = models.CharField(u'Comments', max_length=512, default='', blank=True, null=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)


#重做单信息ranhy
class RemakeOrderCart(models.Model):
        class Meta:
            db_table = 'pg_order_remake_cart'
        order_number = models.CharField(u'Order Number', max_length=64, default='', blank=True, null=True)
        item_id = models.CharField(u'Items ID', max_length=64, default='', null=True, blank=True)
        profile_id = models.CharField(u'Profile ID', max_length=64, default='', null=True, blank=True)
        profile_prescription_id = models.CharField(u'Profile Prescription ID', max_length=64, default='', null=True, blank=True)
        glasses_prescription_id = models.CharField(u'Glasses Prescription ID', max_length=64, default='', null=True, blank=True)
        #分别存储购物车json，验光单json
        item_options = models.TextField(u'Item Options', default='', null=True, blank=True)
        profile_prescription_options = models.TextField(u'Item Options', default='', null=True, blank=True)
        glasses_prescription_options = models.TextField(u'Item Options', default='', null=True, blank=True)
        #数量
        items_count  = models.IntegerField(u'Item Count', default=0,null=True, blank=True)
        original_profile_prescription_id = models.CharField(u'Original Profile Prescription ID', max_length=64, default='', null=True,
                                                   blank=True)
        # original_glasses_prescription_id = models.CharField(u'Original Glasses Prescription ID', max_length=64, default='', null=True,
        #                                            blank=True)
        original_is_norx = models.BooleanField(u'Original NonRx', default=False)
        #是否是norx
        is_norx = models.BooleanField(u'Is NonRx', default=False)
        #是否已生成订单
        is_remake = models.BooleanField(u'Is Remake', default=False)
        remake_order = models.CharField(u'Remake Order', max_length=256, default='', null=True, blank=True)
        user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True, editable=False)
        user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True, editable=False)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)



# Create your models here.
class PgOrderItem(OrderBaseTypeExtends):
    def __str__(self):
        return str(self.id) + ' : ' + self.order_number

    STATUS_CHOICES = PG_ORDER_STATUS_CHOICES

    #  Type
    SHIP_DIRECTION_CHOICES = (
        ('STANDARD', 'Standard'),
        ('EXPRESS', 'Express'),
        ('EMPLOYEE', 'Employee'),
        ('FLATRATE', 'Flatrate'),
        ('CA_EXPRESS', 'Canda_Express')
    )
    # 原垂直棱镜方向保留up&down 向下兼容
    BASE_CHOICES = (
        ('', ''),
        ('IN', 'In'),
        ('OUT', 'Out'),
        ('UP', 'Up(Deprecated)'),
        ('DOWN', 'Down(Deprecated)')
    )
    # 拓展垂直棱镜方向字段
    BASE_CHOICES_V = (
        ('', ''),
        ('UP', 'Up'),
        ('DOWN', 'Down')
    )
    PRESCRIPTION_CHOICES = (
        ('', 'NULL'),
        ('N', '平光'),
        ('S', '单光'),
        ('P', '渐进')
    )
    USED_FOR_CHOICES = (
        ('', 'NULL'),
        ('PROGRESSIVE', '渐进'),
        ('DISTANCE', '驾驶'),
        ('READING', '阅读')
    )
    HANDLING_CHOICES = (
        ('0', '无'),
        ('1', '平衡配重'),
        ('2', '抛光'),
        ('3', '美薄')
    )
    CHANNEL_CHOICES = (
        ('', 'NULL'),
        ('FH15', 'FH15'),
        ('FH17', 'FH17'),
        ('FH19', 'FH19'),
        ('FH21', 'FH21'),
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='PORL', editable=False)  # 订单
    # General
    chanel = models.CharField(u'Chanel', max_length=128, default='WEBSITE', null=True ,blank=True)

    is_vip = models.BooleanField(u'Is VIP', default=False)
    status = models.CharField(u'Status', max_length=128, default='', null=True, choices=STATUS_CHOICES)
    lab_status = models.CharField(u'Lab Status', max_length=128, null=True, blank=True, default='',
                                  choices=LAB_STATUS_CHOICES_EN)

    ship_direction = models.CharField(u'Ship Direction', max_length=40, default='STANDARD',
                                      choices=SHIP_DIRECTION_CHOICES)

    # 2019.12.18 by guof. OMS-541
    # 增加三个字段
    type_id = models.CharField(u'Type Id', max_length=128, default='configurable', null=True)
    attribute_set_id = models.CharField(u'Attribute Set Id', max_length=128, default='13', null=True)
    attribute_set_name = models.CharField(u'Attribute Set Name', max_length=128, default='Glasses', null=True)

    item_id = models.CharField(u'Item Id', max_length=128, default='', null=True)
    product_id = models.CharField(u'Product Id', max_length=128, default='', null=True)

    order_create_at = models.DateTimeField(null=True, blank=True, editable=False)
    order_date = models.DateField(null=True, blank=True)

    order_datetime = models.DateTimeField(null=True, blank=True)

    pg_order_entity = models.ForeignKey(PgOrder, models.SET_NULL,
                                        blank=True,
                                        null=True, )
    lab_order_entity = models.ForeignKey(LabOrder, models.SET_NULL,
                                         blank=True,
                                         null=True, )
    lab_order_number = models.CharField(u'Lab Number', max_length=128, default='', null=True, blank=True)
    comments = models.TextField(u'Comments', max_length=512, default='', null=True, blank=True)

    pupils_position = models.IntegerField(u'Pupils Position', default=0)
    pupils_position_name = models.CharField(u'Pupils Position Name', max_length=255, default='', null=True, blank=True)

    # Lines
    product_index = models.IntegerField(u'Product Index', default=0)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True)
    name = models.CharField(u'Name', max_length=512, default='', null=True, blank=True)
    size = models.CharField(u'Size', max_length=40, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=1)

    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True)
    lens_name = models.CharField(u'Lens Name', max_length=512, default='', null=True, blank=True)

    coating_sku = models.CharField(u'Coating Sku', max_length=128, default='VCAS', null=True, blank=True)
    coating_name = models.CharField(u'Coating Name', max_length=512, default='VCAS', null=True, blank=True)

    tint_sku = models.CharField(u'Tint Sku', max_length=128, default='', null=True, blank=True)
    tint_name = models.CharField(u'Tint Name', max_length=512, default='', null=True, blank=True)

    pal_design_sku = models.CharField(u'PAL Design Sku', max_length=128, default='', null=True, blank=True)
    pal_design_name = models.CharField(u'PAL Design Name', max_length=512, default='', null=True, blank=True)

    dia_1 = models.DecimalField(u'直径1', max_digits=10, decimal_places=2, default=0)
    dia_2 = models.DecimalField(u'直径2', max_digits=10, decimal_places=2, default=0)

    # Prescription
    profile_id = models.CharField(u'Profile ID', max_length=128, default='', null=True, blank=True)

    profile_name = models.CharField(u'Profile Name', max_length=255, default='', null=True,
                                    blank=True)
    profile_prescription_id = models.CharField(u'Profile Prescription ID', max_length=128, default='', null=True,
                                               blank=True)
    od_sph = models.DecimalField(u'Sph(OD)', max_digits=5, decimal_places=2, default=0)
    od_cyl = models.DecimalField(u'Cyl(OD)', max_digits=5, decimal_places=2, default=0)
    od_axis = models.DecimalField(u'Axis(OD)', max_digits=5, decimal_places=0, default=0)
    os_sph = models.DecimalField(u'Sph(OS)', max_digits=5, decimal_places=2, default=0)
    os_cyl = models.DecimalField(u'Cyl(OS)', max_digits=5, decimal_places=2, default=0)
    os_axis = models.DecimalField(u'Axis(OS)', max_digits=5, decimal_places=0, default=0)

    pd = models.DecimalField(u'PD', max_digits=5, decimal_places=1, default=0)
    is_singgle_pd = models.BooleanField(u'Is Single PD', default=True)
    od_pd = models.DecimalField(u'PD(OD)', max_digits=5, decimal_places=1, default=0)
    os_pd = models.DecimalField(u'PD(OS)', max_digits=5, decimal_places=1, default=0)

    # Prescription extends

    od_add = models.DecimalField(u'ADD(OD)', max_digits=5, decimal_places=2, default=0)
    os_add = models.DecimalField(u'ADD(OS)', max_digits=5, decimal_places=2, default=0)

    od_prism = models.DecimalField(u'Prism-h(OD)', max_digits=5, decimal_places=2, default=0)
    od_base = models.CharField(u'Base-h(OD)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES)
    os_prism = models.DecimalField(u'Prism-h(OS)', max_digits=5, decimal_places=2, default=0)
    os_base = models.CharField(u'Base-h(OS)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES)

    # 拓展 垂直棱镜屈光度 和 垂直棱镜方向 (原 棱镜屈光度 和 棱镜方向)
    od_prism1 = models.DecimalField(u'Prism-v(OD)', max_digits=5, decimal_places=2, default=0)
    od_base1 = models.CharField(u'Base-v(OD)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES_V)
    os_prism1 = models.DecimalField(u'Prism-v(OS)', max_digits=5, decimal_places=2, default=0)
    os_base1 = models.CharField(u'Base-v(OS)', max_length=40, null=True, blank=True, default='', choices=BASE_CHOICES_V)

    # New
    country = models.CharField(u'Country', max_length=20, null=False, blank=False, default='US')
    city = models.CharField(u'City', max_length=60, null=True, blank=True, default='')
    region = models.CharField(u'Region', max_length=60, null=True, blank=True, default='')
    # 是否有图片标志
    is_has_imgs = models.BooleanField(u'有无图片', default=False)
    image = models.CharField(u'Image', max_length=1024, default='', null=True, blank=True)
    thumbnail = models.CharField(u'Thumbnail', max_length=1024, default='', null=True, blank=True)
    order_image_urls = models.CharField(u'Order Image URLS', max_length=4000, default='', null=True, blank=True,
                                        editable=False)

    shipping_method = models.CharField(u'Shipping Method', max_length=128, null=True, blank=True, default='')
    shipping_description = models.CharField(u'Shipping Description', max_length=40, null=True, blank=True, default='')

    # jo-9
    prescription_id = models.CharField(u'RXID', max_length=40, null=True, blank=True, default='')
    prescription_name = models.CharField(u'验光单', max_length=128, null=True, blank=True, default='')
    prescription_type = models.CharField(u'验光单类型', max_length=128, null=True, blank=True, default='',
                                         choices=PRESCRIPTION_CHOICES)
    used_for = models.CharField(u'用途', max_length=40, null=True, blank=True, default='', choices=USED_FOR_CHOICES)

    is_shiped_api = models.BooleanField(u'API', default=False)

    qty_ordered = models.IntegerField(u'QTY ORDERED', default=0)

    original_price = models.DecimalField(u'Original Price', max_digits=10, decimal_places=2, default=0)
    price = models.DecimalField(u'Price', max_digits=10, decimal_places=2, default=0)
    base_discount_amount_item = models.DecimalField(u'Base Discount Amount Item', max_digits=10, decimal_places=2,
                                                    default=0)

    estimated_ship_date = models.DateTimeField(u'Est Ship Date', null=True, blank=True)
    estimated_date = models.DateTimeField(u'Est Date', null=True, blank=True)
    final_date = models.DateTimeField(u'Act Ship Date', null=True, blank=True)
    targeted_ship_date = models.DateTimeField(u'Targeted Ship Date', null=True, blank=True)
    promised_ship_date = models.DateTimeField(u'Promised Ship Date', null=True, blank=True)

    instruction = models.TextField(u'Instruction', null=True, blank=True, default='')

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    # add lee 2018.8.21 添加progressive_type字段
    progressive_type = models.CharField(u'Progressive Type', max_length=128, null=True, blank=True)

    # 为渐进镜片定义的瞳高字段
    lab_seg_height = models.CharField(u'Lab Seg Height', max_length=64, default='', null=True, blank=True)
    assemble_height = models.CharField(u'Assemble Height', max_length=32, default='', null=True, blank=True)
    # 为平顶双光镜片定义的子镜高度字段
    sub_mirrors_height = models.CharField(u'Sub-mirrors Height', max_length=16, default='', null=True, blank=True)
    # 镜片的其他特殊处理要求
    special_handling = models.CharField(u'Special Handling', max_length=512, default='', null=True, blank=True)
    # 为美薄处理定义的相关字段 与上面的special_handling不同
    special_handling_sku = models.CharField(u'Special Handling Sku', max_length=128, default='', null=True, blank=True)
    special_handling_name = models.CharField(u'Special Handling Name', max_length=512, default='', null=True,
                                             blank=True)
    #Warranty add by ranhy 2019-9-2
    warranty = models.DecimalField(u'Warranty', max_digits=12, decimal_places=4, default=0,null=True, blank=True)
    row_total_without_warranty = models.DecimalField(u'Row Total Without Warranty', max_digits=12, decimal_places=4, default=0,null=True, blank=True)
    has_warranty = models.BooleanField(u'Has Warranty',default=False)
    is_nonPrescription = models.BooleanField(u'IS NORX',default=False)
    product_options = models.TextField(u'Product Options', default='', null=False, blank=True)

    # 通道字段
    channel = models.CharField(u'Channel', max_length=32, default='', blank=True, null=True, choices=CHANNEL_CHOICES)
    so_type = models.CharField(u'So Type', max_length=128, default='', null=True)

    @property
    def get_dia_1(self):
        # if self.lab_order_entity:
        #     return self.lab_order_entity.dia_1
        # else:
        #     return None
        return self.dia_1

    @property
    def get_dia_2(self):
        return self.dia_2

        if self.lab_order_entity:
            return self.lab_order_entity.dia_2
        else:
            return None

    @property
    def get_mono_pd_off_ctr_mm(self):  # 框心距与瞳距差值
        pd = self.pd
        if not self.is_singgle_pd:
            pd = self.od_pd + self.os_pd

        return self.lens_width + self.bridge - pd

    @property
    def frame_image(self):
        return PRODUCT_IMAGE_PREPATH + self.thumbnail

    def add_activities(self,
                       action_value,
                       user_entity,
                       user_name,
                       comments
                       ):
        logging.debug("add_activities->action_value==>" + str(action_value))
        logging.debug("add_activities->user_entity==>" + str(user_entity))
        logging.debug("add_activities->user_name==>" + str(user_name))
        logging.debug("add_activities->comments==>" + str(comments))

        oa = OrderActivity()
        try:

            oa.add_activity(self.type, self.id, self.order_number, action_value, user_entity, user_name, comments)

            # self.comments=comments
            # self.save()
            return "Success"
        except Exception as e:
            logging.debug("Error==>" + str(e))
            return str(e)

    def generate_lab_orders(self):
        pgo = self
        logging.debug('begin ....')
        if pgo.lab_order_number is None or pgo.lab_order_number == '':
            lbo = None
            from vendor.contollers import lens_order_contoller

            # 2019.12.25 by guof. OMS-544
            # 根据 Attribute Set Name，决定直接生成Accs Order，而不是Lab Order
            # 2019.12.26 by guof. OMS-544
            # 凡是Accs Order，不再根据数量进行拆分
            blue_glasses_list = [item.frame for item in BlueGlasses.objects.filter(is_enabled=True)]
            poc = pgorder_frame_controller()
            if self.lens_sku in blue_glasses_list:
                res_rm = poc.get_lab_frame({"pg_frame": self.frame})
                lab_frame = res_rm.obj['lab_frame'] + 'U'
                from wms.models import inventory_struct_warehouse
                isws = inventory_struct_warehouse.objects.filter(sku=lab_frame, warehouse_code='US-AC01')
                if len(isws) > 0:
                    isw = isws[0]
                    quantity = isw.quantity
                    diff_quantity = quantity - self.quantity
                    if diff_quantity > 0:
                        is_nrx_flag = True
                    else:
                        is_nrx_flag = False
                else:
                    is_nrx_flag = False

            elif self.so_type == 'frame_only':
                res_rm = poc.get_lab_frame({"pg_frame": self.frame})
                lab_frame = res_rm.obj['lab_frame']
                from wms.models import inventory_struct_warehouse
                isws = inventory_struct_warehouse.objects.filter(sku=lab_frame, warehouse_code='US-AC01')
                if len(isws) > 0:
                    isw = isws[0]
                    quantity = isw.quantity
                    diff_quantity = quantity - self.quantity
                    if diff_quantity > 0:
                        is_nrx_flag = True
                    else:
                        is_nrx_flag = False
                else:
                    is_nrx_flag = False

            elif self.attribute_set_name not in ['Glasses', 'Goggles']:
                is_nrx_flag = True
            else:
                is_nrx_flag = False

            #if not ((self.attribute_set_name == 'Goggles' or (self.attribute_set_name == 'Glasses' and self.lens_sku not in blue_glasses_list)) and self.so_type != 'frame_only'):
            if is_nrx_flag:
                aoc = AccsOrderController()

                #lab_order_number = self.__generate_lab_order_number()#self.product_index
                for i in range(self.quantity):
                    data = {}
                    #data['lab_number'] = lab_order_number
                    data['index'] = i
                    data['pg_order_item_entity'] = self.__dict__
                    data['pg_order_item'] = self

                    rm = aoc.add(None, data)
                return 0
            else:
                if self.quantity > settings.LABORDER_BATCH_LIMIT:
                    lbo = self.generate_lab_order()
                else:
                    for i in range(self.quantity):
                        lbo = self.generate_lab_order(i)
                        logging.debug('index: %d' % i)

            '''
            2019.04.11 by guof.
            使用自动分单程序后，不再自动生成Lens Order
            loc = lens_order_contoller()
            paras = {}
            paras['lbo'] = lbo
            loc.create(paras)
            '''
            return 0
        else:
            msg = 'Nothing to do!'
            return -1

    def generate_lab_order_number(self, index=0):
        # Generate lab_orders_number
        # Set Order Number Length Default Value.
        order_number_length = 5
        try:
            order_number_length = ORDER_NUMBER_LENGTH
        except Exception as ex:
            logging.debug(str(ex))
            order_number_length = 5
            pass

        order_number = self.order_number
        order_number_part = order_number[len(order_number) - order_number_length:len(order_number)]
        order_date = self.order_date
        print
        timezone.now()

        year = order_date.year
        str_year = str(year)
        year_part = str_year[len(str_year) - 1:len(str_year)]
        month = order_date.month
        str_month = str(month)
        if len(str_month) == 1:
            str_month = '0' + str_month
        day = order_date.day
        str_day = str(day)
        if len(str_day) == 1:
            str_day = '0' + str_day
        blue_glasses_list = [item.frame for item in BlueGlasses.objects.filter(is_enabled=True)]
        pgorderitems = PgOrderItem.objects.filter(order_number=self.order_number)
        total = 0
        for item in pgorderitems:
            ##if (item.attribute_set_name == 'Goggles' or (item.attribute_set_name == 'Glasses' and item.lens_sku not in blue_glasses_list)) and item.so_type != 'frame_only':
            #if item.attribute_set_name == 'Glasses' or item.attribute_set_name == 'Goggles':
            total = total + item.quantity
            ##else:
            ##    total = total + 1
        #total = int(self.pg_order_entity.total_qty_ordered)
        logging.debug("total==>%s" % total)


        # if index > 0:
        #     #pgorderitems_list = PgOrderItem.objects.filter(order_number=self.order_number).order_by("-product_index")
        #     str_product_index = 1 + index + self.product_index
        #     lab_order_number = year_part + str_month + str_day + '-' + order_number_part + '-' + str(str_product_index) + "T" + str(total)
        # else:
        if self.product_index == 0:
            product_index = self.product_index + 1
        else:
            product_index = self.product_index
        lab_order_number = year_part + str_month + str_day + '-' + order_number_part + '-' + str(product_index) + "T" + str(total)

        return lab_order_number

    def generate_lab_order(self, index=0, flag='lab'):

        pgo = self
        logging.debug('internal method.')

        lab_order_number = self.generate_lab_order_number(index)

        # print (lab_order_number)

        lbo = LabOrder()
        # General
        lbo.lab_number = lab_order_number
        lbo.order_number = self.order_number
        lbo.priority = self.priority
        lbo.base_entity = self.id

        lbo.chanel = self.chanel
        lbo.is_vip = self.is_vip
        lbo.tag = self.tag
        lbo.ship_direction = self.ship_direction
        lbo.act_ship_direction = self.ship_direction

        lbo.order_date = self.order_date
        lbo.order_datetime = self.order_datetime
        lbo.comments = self.comments
        lbo.comments_inner = self.comments_inner

        lbo.pupils_position = self.pupils_position
        lbo.pupils_position_name = self.pupils_position_name

        lbo.lens_height = self.lens_height
        lbo.bridge = self.bridge
        lbo.lens_width = self.lens_width
        lbo.temple_length = self.temple_length
        lbo.is_has_nose_pad = self.is_has_nose_pad

        lbo.lens_seght = self.lens_seght
        lbo.asmbl_seght = self.asmbl_seght
        lbo.lab_seg_height = self.lab_seg_height
        lbo.assemble_height = self.assemble_height
        lbo.special_handling = self.special_handling
        lbo.sub_mirrors_height = self.sub_mirrors_height
        lbo.channel = self.channel

        lbo.profile_id = self.profile_id
        lbo.profile_name = self.profile_name
        lbo.prescription_id = self.profile_prescription_id
        # 将pg order item中的frame的第一个数字存储到lab order的category_id字段中
        lbo.category_id = self.frame[0]

        # 太阳镜 start ===============================================
        # 按镜架SKU位数判断是否为太阳镜
        poc = pgorder_frame_controller()
        res_rm = poc.get_lab_frame({"pg_frame":self.frame})
        if res_rm.obj['sg_flag']:
            isplr_data = '{"sku":"%s"}' % self.lens_sku
            try:
                isplr_req = urllib2.Request(
                    url=PG_SYNC_IS_POLARIZED_URL,
                    data=isplr_data,
                    headers={'Content-Type': 'application/json'}
                )
                isplr_res = urllib2.urlopen(isplr_req)
                json_res = json.loads(isplr_res.read())

                r_code = json_res.get('code')
                r_is_polarized = json_res.get('is_polarized')
                r_sku = json_res.get('sku')
                color_char = res_rm.obj['lens_color']#self.frame[-1]

            except Exception as e:
                logging.debug("Request fail==>%s" % e)

            if r_code == 1:  # 找到对应lens_sku正常返回
                # 通过lesn_option判断是 偏光/实色染色
                try:
                    if r_is_polarized == False or r_is_polarized == 'False':
                        # 镜片为实色染色 ========= 染色SKU格式写死 TS- =========
                        new_lens_sku = 'TS-%s' % color_char
                        # 染色信息在lab_product里
                        otint = PgProduct.objects.get(sku=new_lens_sku)
                        lbo.tint_sku = otint.lab_product.sku
                        lbo.tint_name = otint.lab_product.name
                        # 镜片信息也在lab_product里 需要通过镜片SKU再查一遍
                        olens = PgProduct.objects.get(sku=self.lens_sku)
                        lbo.lens_sku = olens.lab_product.sku
                        lbo.lens_name = olens.lab_product.name
                        lbo.act_lens_sku = olens.lab_product.sku
                        lbo.act_lens_name = olens.lab_product.name
                    else:
                        # 如果是偏光镜片 需要把镜架最后的颜色字符拼接到镜片SKU上 并去掉前面'S'字符
                        new_lens_sku = '%s%s' % (self.lens_sku[1:], color_char)
                        olens = PgProduct.objects.get(sku=new_lens_sku)
                        # 镜片信息
                        lbo.lens_sku = olens.lab_product.sku
                        lbo.lens_name = olens.lab_product.name
                        lbo.act_lens_sku = olens.lab_product.sku
                        lbo.act_lens_name = olens.lab_product.name
                        # 偏光镜片的染色信息为空
                        # lbo.tint_sku = olens.lab_product.sku
                        # lbo.tint_name = olens.lab_product.name
                except:
                    self.comments = '镜片信息未找到'
                    self.save()

                # 处理镜架SKU 去掉前后位
                oframe = self.frame[1:-1]
                lbo.frame = oframe

            elif r_code == -1:
                logging.debug(json_res.message)

        else:
            # 如果不是太阳镜走正常流程
            if self.lens_sku <> None:
                if self.lens_sku <> '':
                    olens = PgProduct.objects.get(sku=self.lens_sku)
                    lbo.lens_sku = olens.lab_product.sku
                    lbo.lens_name = olens.lab_product.name
                    lbo.act_lens_sku = olens.lab_product.sku
                    lbo.act_lens_name = olens.lab_product.name

            if self.tint_sku <> None:
                if self.tint_sku <> '':
                    otint = PgProduct.objects.get(sku=self.tint_sku)
                    lbo.tint_sku = otint.lab_product.sku
                    lbo.tint_name = otint.lab_product.name

            oframe = res_rm.obj['lab_frame']#self.frame[1:len(self.frame)]
            lbo.frame = oframe

        # 太阳镜 end ===============================================

        # Lines
        lbo.name = self.name
        lbo.size = self.size
        lbo.frame_type = self.frame_type
        lbo.color = self.color

        if self.quantity > settings.LABORDER_BATCH_LIMIT:
            lbo.quantity = self.quantity
        else:
            lbo.quantity = 1

        if self.coating_sku <> None:
            if self.coating_sku <> '':
                ocoating = PgProduct.objects.get(sku=self.coating_sku)
                if lbo.lens_sku not in ['KD56'] and self.coating_sku == 'VCAS':
                    # if (lbo.lens_sku == 'CD56' and abs(float(lbo.os_sph))<=4 and
                    #         abs(float(lbo.od_sph))<=4 and abs(float(lbo.os_cyl)) <=3 and
                    #         abs(float(lbo.od_cyl)) <=3 and
                    #         (self.tint_sku=='' or self.tint_sku == None)):
                    #     lbo.coating_sku = ocoating.lab_product.sku
                    #     lbo.coating_name = ocoating.lab_product.name
                    # else:
                    lbo.coating_sku = 'HMC'
                    lbo.coating_name = '涂层-HMC'
                else:
                    lbo.coating_sku = ocoating.lab_product.sku
                    lbo.coating_name = ocoating.lab_product.name

        if self.pal_design_sku <> None:
            if self.pal_design_sku <> '':
                odesign = PgProduct.objects.get(sku=self.pal_design_sku)
                lbo.pal_design_sku = odesign.lab_product.sku
                lbo.pal_design_name = odesign.lab_product.name

        # Prescription
        lbo.od_sph = self.od_sph
        lbo.od_cyl = self.od_cyl
        lbo.od_axis = self.od_axis
        lbo.os_sph = self.os_sph
        lbo.os_cyl = self.os_cyl
        lbo.os_axis = self.os_axis

        # if lbo.od_cyl > 0
        '''
        新的sph=旧的sph+旧的cyl，新的cyl=-旧的cyl，新的轴位=旧的轴位-90°(轴位＞90°)，新的轴位=180°-90°(如果轴位＜90度)，如果轴位=90°，不变

        第二个版本：
        新的sph=旧的sph+旧的cyl，新的cyl=-旧的cyl，新的轴位=旧的轴位-90°(轴位＞90°)，新的轴位=旧的轴位+90°(如果轴位＜90度)，如果轴位=90°，新的轴位=180°。
        '''
        if float(self.od_cyl) > 0:
            pres = PrescriptionSwap()
            pres = self.convert_cyl_plus(self.od_sph, self.od_cyl, self.od_axis)
            lbo.od_sph = pres.sph
            lbo.od_cyl = pres.cyl
            lbo.od_axis = pres.axis

        if float(self.os_cyl) > 0:
            pres = PrescriptionSwap()
            pres = self.convert_cyl_plus(self.os_sph, self.os_cyl, self.os_axis)
            lbo.os_sph = pres.sph
            lbo.os_cyl = pres.cyl
            lbo.os_axis = pres.axis

        lbo.pd = self.pd
        lbo.is_singgle_pd = self.is_singgle_pd
        lbo.od_pd = self.od_pd
        lbo.os_pd = self.os_pd

        # Prescription extends
        lbo.od_add = self.od_add
        lbo.os_add = self.os_add
        lbo.od_prism = self.od_prism
        lbo.od_base = self.od_base
        lbo.os_prism = self.os_prism
        lbo.os_base = self.os_base

        lbo.od_prism1 = self.od_prism1
        lbo.od_base1 = self.od_base1
        lbo.os_prism1 = self.os_prism1
        lbo.os_base1 = self.os_base1

        prescri = Prescription()
        prescri.rsph = self.od_sph
        prescri.lsph = self.os_sph
        prescri.rcyl = self.od_cyl
        prescri.lcyl = self.os_cyl
        prescri.rax = self.od_axis
        prescri.lax = self.os_axis
        prescri.rpri = self.od_prism
        prescri.lpri = self.os_prism
        prescri.rbase = self.od_base
        prescri.lbase = self.os_base

        prescri.rpri1 = self.od_prism1
        prescri.rbase1 = self.od_base1
        prescri.lpri1 = self.os_prism1
        prescri.lbase1 = self.os_base1

        prescri.radd = self.od_add
        prescri.ladd = self.os_add
        prescri.pd = self.pd
        if self.is_singgle_pd:
            prescri.single_pd = "1"
        else:
            prescri.single_pd = "0"
        prescri.rpd = self.od_pd
        prescri.lpd = self.os_pd

        pre = utilities.convert_to_dict(prescri)

        logging.debug("pre==>%s" % pre)

        body = {
            "product_sku": self.frame,
            "prescription": pre
        }
        body = json.dumps(body, cls=DateEncoder)

        logging.debug("body==>%s" % body)

        req = urllib2.Request(url=CALCULATE_DIAMETER_URL, data=body, headers=token_header)
        logging.debug("url==>%s" % CALCULATE_DIAMETER_URL)
        res = urllib2.urlopen(req)
        resp = res.read()
        logging.debug("返回结果体。。。。。。")
        logging.debug("resp==>%s" % resp)
        if resp == "1":
            logging.info("Error lab_order_number CALCULATE_DIAMETER ==>%s" % lab_order_number)

        resp = json.loads(resp)
        logging.debug("dia_1==>%s" % resp['dia_1'])
        lbo.dia_1 = resp['dia_1']
        lbo.dia_2 = resp['dia_2']
        # add lee 2018.8.21
        lbo.used_for = self.used_for
        lbo.prescription_name = self.prescription_name
        lbo.prescription_type = self.prescription_type
        lbo.progressive_type = self.progressive_type
        # 美薄特殊处理
        lbo.special_handling_sku = self.special_handling_sku
        lbo.special_handling_name = self.special_handling_name
        # end add
        #镜架图片
        lbo.image = self.image
        lbo.thumbnail = self.thumbnail
        lbo.order_type = self.order_type
        lbo.save()

        if flag == 'lab':
            # 判断是否具有accorder
            pg_sql = """SELECT attribute_set_name,frame,quantity FROM oms_pgorderitem WHERE order_number='%s'""" % self.order_number
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(pg_sql)
                pgborderitems = namedtuplefetchall(cursor)
                glasses_len = 0
                accs_comments_ship = ''
                for item in pgborderitems:
                    if item.attribute_set_name == 'Glasses' or item.attribute_set_name == 'Goggles':
                        glasses_len = glasses_len + 1
                    else:
                        psql = """SELECT * FROM wms_product_frame WHERE sku='%s'""" % item.frame
                        cursor.execute(psql)
                        p_product = namedtuplefetchall(cursor)
                        if len(p_product) > 0:
                            product = p_product[0]
                            accs_comments_ship = accs_comments_ship +";"+ "SKU:"+str(item.frame)+"名称:"+str(product.name)+"数量:"+str(item.quantity)
                        else:
                            accs_comments_ship = accs_comments_ship +";"+ "SKU:" + str(item.frame) + "名称:未找到数量:" + str(item.quantity)
            if len(pgborderitems) != glasses_len and glasses_len != 0:
                lbo.comments_ship = '具有AccsOrders' + accs_comments_ship

        # 生成qr等图片
        for code in SCAN_TYPE:
            if code == 'qr':
                utilities.createQR(lab_order_number)
                lbo.qr_path = 'scan/qr/' + lab_order_number + '.png'
            elif code == 'c39':
                utilities.createC39(lab_order_number)
                lbo.c39_path = 'scan/c39/' + lab_order_number + '.png'
            elif code == 'c128':
                bar_img_src = utilities.createC128(str("%s%s" % (settings.BAR_CODE_PREFIX, lbo.id)), lbo.create_at)
                lbo.c128_path = bar_img_src #'scan/c128/' + lab_order_number + '.png'

        lbo.save()
        # 增加在Lab Order成功创建之后，推送至MRP
        # 2019.07.10 by guof.
        try:
            from oms.controllers.lab_order_controller import lab_order_controller
            loc = lab_order_controller()
            loc.post_mrp(lbo)
        except Exception as ex:
            logging.critical(str(ex))

        '''laborder生成targeted_date'''
        self.generate_date(lbo)
        if index == 0:
            self.lab_order_number = lab_order_number
            self.lab_order_entity = lbo
            self.save()

        msg = 'Lab Orders Saved! Pg OrderNumber: %s -> Lab OrderNumber: %s', self.order_number, lbo.lab_number
        return lbo

    def convert_cyl_plus(self, old_sph, old_cyl, old_axis):
        pres = PrescriptionSwap()
        # if lbo.od_cyl > 0
        '''
        新的sph=旧的sph+旧的cyl，新的cyl=-旧的cyl，新的轴位=旧的轴位-90°(轴位＞90°)，新的轴位=180°-90°(如果轴位＜90度)，如果轴位=90°，不变
        第二个版本：
        新的sph=旧的sph+旧的cyl，新的cyl=-旧的cyl，新的轴位=旧的轴位-90°(轴位＞90°)，新的轴位=旧的轴位+90°(如果轴位＜90度)，如果轴位=90°，新的轴位=180°。
        '''
        if float(old_cyl) > 0:
            m_sph = float(old_sph) + float(old_cyl)
            m_cyl = float(old_cyl) * -1
            if float(old_axis) > 90:
                m_axis = float(old_axis) - 90
            elif float(old_axis) < 90:
                m_axis = float(old_axis) + 90
            elif float(old_axis) == 90:
                m_axis = 180

            pres.sph = m_sph
            pres.cyl = m_cyl
            pres.axis = m_axis
        return pres

    def query_order_item(self, order_number):
        queryset = PgOrderItem.objects.filter(order_number=order_number)
        results = serializers.serialize('json', queryset)
        return results

    def generate_date(self, laborder):
        hs = HolidaySetting()
        us_holiday = hs.holiday(laborder.create_at)
        if laborder.lens_sku:
            sku = laborder.lens_sku
            lp = LabProduct.objects.get(sku=sku)
            logging.debug("------------------" + str(us_holiday))
            if not lp.is_rx_lab and laborder.ship_direction <> 'EMPLOYEE':
                delta_day = 2
                # targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                targeted_date = laborder.create_at + datetime.timedelta(days=delta_day)
                estimated_date = laborder.create_at + datetime.timedelta(days=delta_day + 1)
                intersection_date = self.inter_day(laborder.create_at, targeted_date, us_holiday)
                delta_day += len(intersection_date)
                targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                laborder.targeted_date = targeted_date
                laborder.estimated_date = estimated_date
                laborder.save()
            elif lp.is_rx_lab and laborder.ship_direction == 'EXPRESS':
                delta_day = 3
                targeted_date = laborder.create_at + datetime.timedelta(days=delta_day)
                estimated_date = laborder.create_at + datetime.timedelta(days=delta_day + 1)
                intersection_date = self.inter_day(laborder.create_at, targeted_date, us_holiday)
                delta_day += len(intersection_date)
                targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                laborder.targeted_date = targeted_date
                laborder.estimated_date = estimated_date
                laborder.save()
            elif lp.is_rx_lab and laborder.ship_direction == 'STANDARD':
                delta_day = 4
                targeted_date = laborder.create_at + datetime.timedelta(days=delta_day)
                estimated_date = laborder.create_at + datetime.timedelta(days=delta_day + 1)
                intersection_date = self.inter_day(laborder.create_at, targeted_date, us_holiday)
                delta_day += len(intersection_date)
                targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                laborder.targeted_date = targeted_date
                laborder.estimated_date = estimated_date
                laborder.save()
            elif laborder.ship_direction == 'EMPLOYEE':
                delta_day = 5
                targeted_date = laborder.create_at + datetime.timedelta(days=delta_day)
                estimated_date = laborder.create_at + datetime.timedelta(days=delta_day + 1)
                intersection_date = self.inter_day(laborder.create_at, targeted_date, us_holiday)
                delta_day += len(intersection_date)
                targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                laborder.targeted_date = targeted_date
                laborder.estimated_date = estimated_date
                laborder.save()
        else:
            if laborder.ship_direction == 'EXPRESS':
                delta_day = 3
                targeted_date = laborder.create_at + datetime.timedelta(days=delta_day)
                estimated_date = laborder.create_at + datetime.timedelta(days=delta_day + 1)
                intersection_date = self.inter_day(laborder.create_at, targeted_date, us_holiday)
                delta_day += len(intersection_date)
                targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                laborder.targeted_date = targeted_date
                laborder.estimated_date = estimated_date
                laborder.save()
            elif laborder.ship_direction == 'STANDARD':
                delta_day = 4
                targeted_date = laborder.create_at + datetime.timedelta(days=delta_day)
                estimated_date = laborder.create_at + datetime.timedelta(days=delta_day + 1)
                intersection_date = self.inter_day(laborder.create_at, targeted_date, us_holiday)
                delta_day += len(intersection_date)
                targeted_date = (laborder.create_at + datetime.timedelta(days=delta_day)).strftime("%Y-%m-%d %H:%M:%S")
                laborder.targeted_date = targeted_date
                laborder.estimated_date = estimated_date
                laborder.save()

    def inter_day(self, begin, end, holiday):
        # begin = str(begin).split("+")[0]
        # end = str(end).split("+")[0]
        date_list = []
        # begin_date = datetime.datetime.strptime(str(begin), "%Y-%m-%d")
        begin_date = begin.strftime("%Y-%m-%d")
        # end_date = datetime.datetime.strptime(str(end), "%Y-%m-%d")
        end_date = end.strftime("%Y-%m-%d")
        while begin_date <= end_date:
            date_list.append(begin_date)
            begin_date = datetime.datetime.strptime(begin_date, "%Y-%m-%d")
            begin_date += datetime.timedelta(days=1)
            begin_date = begin_date.strftime("%Y-%m-%d")
        intersection_date = list(set(holiday).intersection(set(date_list)))
        return intersection_date

    """通过pk查找object"""

    def query_by_id(self, pk):
        poi = PgOrderItem.objects.get(pk=pk)
        return poi

    '''通过lab_order查找object'''

    def query_by_labOrder(self, lab_order):
        poi = PgOrderItem.objects.get(pk=lab_order)
        return poi

    """通过order_number过滤objects"""

    def filter_by_id(self, order_number):
        pois = PgOrderItem.objects.filter(order_number=order_number)
        return pois

    """修改status"""

    def modify_status(self, order_number, action_value):
        pois = PgOrderItem.objects.filter(order_number=order_number)
        status = action_value.lower()
        for poi in pois:
            poi.status = status
            poi.save()
        return pois

    """判断pgorderitem所对应的laborder的状态是否是发货"""

    def judge_status(self, pois):
        flag = True
        for poi in pois:
            if poi.lab_order_entity.status <> "SHIPPING":
                flag = False
        return flag

    @property
    def get_prescritpion(self):
        pre = Prescription()
        pre.rsph = self.od_sph
        pre.lsph = self.os_sph
        pre.rcyl = self.od_cyl
        pre.lcyl = self.os_cyl
        pre.rax = self.od_axis
        pre.lax = self.os_axis
        pre.rpri = self.od_prism
        pre.lpri = self.os_prism
        pre.rbase = self.od_base
        pre.lbase = self.os_base
        pre.rpri1 = self.od_prism1
        pre.lpri1 = self.os_prism1
        pre.rbase1 = self.od_base1
        pre.lbase1 = self.os_base1
        pre.radd = self.od_add
        pre.ladd = self.os_add
        pre.used_for = self.used_for
        pre.pd = self.pd
        if self.is_singgle_pd:
            pre.single_pd = "1"
        else:
            pre.single_pd = "0"
            pre.rpd = self.od_pd
            pre.lpd = self.os_pd
        return pre


"""PgOrderItem的form类"""


class PgOrderItemFormDetail(ModelForm):
    class Meta:
        model = PgOrderItem
        fields = '__all__'


class PgOrderItemFormDetailParts(ModelForm):
    class Meta:
        model = PgOrderItem
        fields = (
            # Order
            'order_number',
            'lab_status',
            'item_id',
            'product_id',
            'order_date',
            'order_datetime',
            'lab_order_number',
            'comments',
            'pupils_position',
            'pupils_position_name',
            'product_index',
            'instruction',

            # Frame
            'frame',
            'name',
            'quantity',
            'size',
            'lens_width',
            'bridge',
            'temple_length',
            'lens_height',
            'thumbnail',

            # Lens
            'lens_sku',
            'lens_name',
            'coating_sku',
            'coating_name',
            'tint_sku',
            'tint_name',
            'pal_design_sku',
            'pal_design_name',

            # Prescription
            'profile_id',
            'profile_name',
            'is_nonPrescription',
            'product_options',
            'profile_prescription_id',
            'od_sph',
            'od_cyl',
            'od_axis',
            'os_sph',
            'os_cyl',
            'os_axis',
            'pd',
            'is_singgle_pd',
            'od_pd',
            'os_pd',

            # Prescription extends
            'od_add',
            'os_add',
            'od_prism',
            'od_base',
            'os_prism',
            'os_base',
            'od_prism1',
            'od_base1',
            'os_prism1',
            'os_base1',

            'prescription_id',
            'prescription_name',
            'prescription_type',
            'used_for',
            'progressive_type',  # add lee 2018.8.21

            'channel',

        )


class OrderAddtional(BaseType):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OPOA', editable=False)  # 订单附件

    mg_id = models.IntegerField(u'Mg ID', default=0)
    order_entity = models.IntegerField(u'Order Entity', default=0)
    order_item_entity = models.IntegerField(u'Order Item Entity', default=0)
    instruction = models.CharField(u'Instruction', max_length=4000, default='', blank=True, null=True)
    mg_created_at = models.DateTimeField(u'Mg Created At', null=True, blank=True)
    mg_updated_at = models.DateTimeField(u'Mg Updated At', null=True, blank=True)
    is_used = models.BooleanField(u'Is Used', default=False)


class PrescriptionSwap:
    sph = 0.00
    cyl = 0.00
    axis = 0.00


# 评论实体类
class Order_comment:
    def __init__(self, comment, is_visible_on_front=0, is_customer_notified=0, statue="processing",
                 entity_name="order"):
        self.comment = comment
        self.is_visible_on_front = is_visible_on_front
        self.is_customer_notified = is_customer_notified
        self.statue = statue
        self.entity_name = entity_name


class factory(BaseType):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='FACT', editable=False)

    factory_id = models.CharField(u'Factory ID', max_length=64, default='1', blank=True, null=True, unique=True)
    factory_name = models.CharField(u'Factory Name', max_length=255, default='', blank=True, null=True)


class laborder_request_notes(BaseType):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='LORN', editable=False)

    # 最后一个订单的信息
    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)
    lab_number = models.CharField(u'LabOrder Number', max_length=128, default='', blank=True, null=True)

    count = models.IntegerField(u'Count', default=0)

    vendor = models.CharField(u'VD', max_length=128, null=True, blank=True, default='0')

    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
    comments = models.CharField(u'Comments', max_length=512, default='', blank=True, null=True)
    warehouse_code = models.CharField(u'Code', default='', max_length=40)


    @property
    def lines(self):
        lines = laborder_request_notes_line.objects.filter(lrn=self)
        return lines

    @property
    def laborder_entities(self):
        laborder_entities = []
        lines = self.lines
        for line in lines:
            laborder_entities.append(line.laborder_entity)

        return laborder_entities

    @property
    def laborder_entities_frame_outbound(self):
        laborder_entities = []
        lines = self.lines
        for line in lines:
            '''
            q1 = Q()
            q1.connector = 'OR'
            q1.children.append(('status', 'FRAME_OUTBOUND'))
            q1.children.append(('status', 'REQUEST_NOTES'))
            '''
            if line.laborder_entity.status == 'FRAME_OUTBOUND' or \
                    line.laborder_entity.status == 'REQUEST_NOTES':  # 仅生成镜架出库状态的订单
                laborder_entities.append(line.laborder_entity)

        return laborder_entities


class laborder_request_notes_line(BaseType):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='LORL', editable=False)

    lrn = models.ForeignKey(laborder_request_notes, models.CASCADE,
                            blank=True,
                            null=True, editable=False)

    laborder_entity = models.ForeignKey(LabOrder, models.SET_NULL,
                                        blank=True,
                                        null=True, editable=False)

    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)
    index = models.IntegerField(u'Index', default=0)
    frame = models.CharField(u'Fame', max_length=128, default='', blank=True, null=True)
    lab_number = models.CharField(u'Fame', max_length=128, default='', blank=True, null=True, unique=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    lens_type = models.CharField(u'Lens Type', max_length=20, default='', blank=True, null=True)
    order_date = models.DateTimeField(u'Order Date', null=True, blank=True)
    order_created_date = models.DateTimeField(u'Order Created Date', null=True, blank=True)

    vendor = models.CharField(u'Vendor', max_length=128, default='', blank=True, null=True)

    location = models.CharField(u'Location', max_length=128, default='', blank=True, null=True)
    warehouse_code = models.CharField(u'Code', default='', max_length=40)

    @property
    def status(self):
        return self.laborder_entity.status

    @property
    def status_value(self):
        return self.laborder_entity.get_status_display


class construction_voucher(construction_voucher_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OBCV', editable=False)

    request_notes_entity = models.ForeignKey(laborder_request_notes_line, models.SET_NULL,
                                             blank=True,
                                             null=True, editable=False)


class construction_voucher_control:
    def add(self, id, user_entity=None, user_id=-1, user_name='system', comments=''):
        try:
            #cv = construction_voucher.objects.get(lab_number=id)
            cv = self.add_print_times(id, user_entity, user_id, user_name, comments)
            self.__track(id, user_entity, user_id, user_name, comments)
            #print_times = cv.print_times
            #cv.print_times = print_times + 1
            #cv.save()
            return cv
        except:
            #lrn = laborder_request_notes_line.objects.get(lab_number=id)
            cv = self.add_print_times(id, user_entity, user_id, user_name, comments)
            self.__track(id, user_entity, user_id, user_name, comments)
            #cv = construction_voucher()
            #cv.laborder_id = lrn.laborder_id
            #cv.lab_number = lrn.lab_number
            #cv.request_notes_entity = lrn
            #cv.user_id = user_id
            #cv.user_name = user_name
            #cv.comments = comments
            #cv.save()
            return cv

    def add_print_times(self, id, user_entity=None, user_id=-1, user_name='system', comments=''):
        try:
            cv = construction_voucher.objects.get(lab_number=id)
            print_times = cv.print_times
            cv.print_times = print_times + 1
            cv.save()
            return cv
        except:
            lrn = laborder_request_notes_line.objects.get(lab_number=id)
            cv = construction_voucher()
            cv.laborder_id = lrn.laborder_id
            cv.lab_number = lrn.lab_number
            cv.request_notes_entity = lrn
            cv.user_id = user_id
            cv.user_name = user_name
            cv.comments = comments
            cv.save()
            return cv

    def __track(self, id, user_entity=None, user_id=-1, user_name='system', comments=''):
        try:
            from api.controllers.tracking_controllers import tracking_lab_order_controller
            lbo = LabOrder.objects.get(lab_number=id)
            # if lbo.status == '' or lbo.status == 'REQUEST_NOTES' or lbo.status == 'FRAME_OUTBOUND':
            if lbo.status == 'FRAME_OUTBOUND':
                lbo.status = 'PRINT_DATE'
                lbo.save()
                action = 'PRINT_DATE'
                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, user_entity, action)
        except Exception as e:
            print(e)
            logging.debug('exception .... %s' % e.message)
            return


class construction_voucher_finish_glasses(construction_voucher_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OCVF', editable=False)

    request_notes_entity = models.ForeignKey(laborder_request_notes_line, models.SET_NULL,
                                             blank=True,
                                             null=True, editable=False)


class construction_voucher_finish_glasses_control:
    def add(self, id, user_entity=None, user_id=-1, user_name='system', comments=''):
        try:
            with transaction.atomic():
                cv = construction_voucher_finish_glasses.objects.get(lab_number=id)
                self.__track(id, user_entity, user_id, user_name, comments)
                print_times = cv.print_times
                cv.print_times = print_times + 1
                cv.save()
                return cv
        except:
            with transaction.atomic():
                lrn = laborder_request_notes_line.objects.get(lab_number=id)
                self.__track(id, user_entity, user_id, user_name, comments)
                cv = construction_voucher_finish_glasses()
                cv.laborder_id = lrn.laborder_id
                cv.lab_number = lrn.lab_number
                cv.request_notes_entity = lrn
                cv.user_id = user_id
                cv.user_name = user_name
                cv.comments = comments
                cv.save()
                return cv

    def __track(self, id, user_entity=None, user_id=-1, user_name='system', comments=''):
        try:
            from api.controllers.tracking_controllers import tracking_lab_order_controller
            lbo = LabOrder.objects.get(lab_number=id)

            if lbo.status == 'LENS_RECEIVE' or lbo.vendor == '3' or lbo.vendor == '5':  # 增加 Vd3 的判断,特别对待
                lbo.status = 'ASSEMBLING'
                lbo.save()

                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, user_entity, 'ASSEMBLING')

                LabOrder.objects.filter(lab_number=id).update(status='ASSEMBLING')
                # (self,order_number,sku,order_date,lab_order_entity,user_entity,username,action,action_value):

        except Exception as e:
            logging.debug('exception .... %s' % e.message)
            return


#
# from util.base_type import base_type
# class lab_order_generate_log(base_type):
#    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
#    type = models.CharField(u'Type', max_length=20, default='LBOG', editable=False)
#

class laborder_purchase_order(BaseType):
    type = models.CharField(u'类型', max_length=20, default='LOPO', editable=False)

    count = models.IntegerField(u'Count', default=0)
    vendor = models.CharField(u'VD', max_length=128, null=True, blank=True, default='0')
    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)

    @property
    def lines(self):
        lines = laborder_purchase_order_line.objects.filter(lpo=self)
        return lines

    @property
    def laborder_entities(self):
        laborder_entities = []
        lines = self.lines
        for line in lines:
            laborder_entities.append(line.laborder_entity)

        return laborder_entities

    @property
    def laborder_entities_frame_outbound(self):
        laborder_entities = []
        lines = self.lines
        for line in lines:
            if line.laborder_entity.status == 'FRAME_OUTBOUND' or \
                    line.laborder_entity.status == 'REQUEST_NOTES':
                laborder_entities.append(line.laborder_entity)

        return laborder_entities


class laborder_purchase_order_line(BaseType):
    PURCHASE_TYPE_CHOICES = (
        ("LENS", "镜片"),
        ("GLASSES", "成镜"),
        ("ASSEMBLED", "装配")
    )

    type = models.CharField(u'类型', max_length=20, default='LOPL', editable=False)

    lpo = models.ForeignKey(laborder_purchase_order, models.CASCADE, blank=True, null=True, editable=False)
    laborder_entity = models.ForeignKey(LabOrder, models.SET_NULL, blank=True, null=True, editable=False)
    laborder_id = models.IntegerField(u'Entity ID', default=0, unique=True)
    frame = models.CharField(u'Fame', max_length=128, default='', blank=True, null=True)
    lab_number = models.CharField(u'Fame', max_length=128, default='', blank=True, null=True, unique=True)
    quantity = models.IntegerField(u'Quantity', default=0)
    lens_type = models.CharField(u'Lens Type', max_length=20, default='', blank=True, null=True)
    order_date = models.DateTimeField(u'Order Date', null=True, blank=True)
    order_created_date = models.DateTimeField(u'Order Created Date', null=True, blank=True)
    purchase_type = models.CharField(u'Purchase Type', max_length=20, default='LENS', blank=True, null=True,
                                     choices=PURCHASE_TYPE_CHOICES)

    is_set_hours_of_purchase = models.BooleanField(u'Is Set Hours of Purchase', default=False)
    vendor_order_reference = models.CharField(u'工厂订单号', max_length=128, default='', blank=True)
    comments = models.CharField(u'Comments',max_length=1024, default='', blank=True, null=True)

    # 伟星下单相关字段
    @property
    def is_purchased(self):
        if self.vendor_order_reference == '' or self.vendor_order_reference is None:
            return False
        return True

    @property
    def get_wx_tint_type(self):
        if not self.laborder_entity.tint_sku in ('', None):
            # 伟星染色名称 ('标准', '渐层色')
            return '标准' if self.laborder_entity.tint_sku[:2] == 'RS' else '渐层色'
        return ''

    # @property
    # def get_wx_tint_color(self):
    #     return self.laborder_entity.tint_name[-2:] if not self.laborder_entity.tint_name in ('', None) else ''

    @property
    def vendor(self):
        return self.laborder_entity.vendor

    @property
    def status_value(self):
        return self.laborder_entity.get_status_display

    @property
    def status(self):
        return self.laborder_entity.status


# 更改订单状态的申请
class hold_cancel_request(models.Model):
    STATUS_NOW_CHOICES = (
        ('', '新订单'),

        ('REQUEST_NOTES', '出库申请'),
        ('FRAME_OUTBOUND', '镜架出库'),
        ('PRINT_DATE', '镜片生产'),
        # ('TINT', '染色'),
        # ('RX_LAB', '车房'),
        # ('ADD_HARDENED', '加硬'),
        # ('COATING', '加膜'),

        ('LENS_REGISTRATION', '来片登记'),
        # ('INITIAL_INSPECTION', '镜片初检'),
        ('LENS_RETURN', '镜片退货'),
        ('LENS_RECEIVE', '镜片收货'),
        ('ASSEMBLING', '待装配'),
        ('ASSEMBLED', '装配完成'),
        ('GLASSES_RECEIVE', '成镜收货'),

        # ('SHAPING', '整形'),
        ('FINAL_INSPECTION', '终检'),  # 原终检合格
        ('FINAL_INSPECTION_YES', '终检合格'),
        ('FINAL_INSPECTION_NO', '终检不合格'),
        ('GLASSES_RETURN', '成镜返工'),
        # ('PURGING', '清洗'),
        ('COLLECTION', '归集'),
        ('PRE_DELIVERY', '预发货'),
        ('PICKING', '已拣配'),

        ('ORDER_MATCH', '订单配对'),

        # ('PACKAGE', '包装'),
        ('BOXING', '装箱'),
        ('SHIPPING', '已发货'),
        # ('COMPLETE', '完成'),
        ('ONHOLD', '暂停'),
        ('CANCELLED', '取消'),
        ('REDO', '重做'),

        ('R2HOLD', '申请暂停'),
        ('R2CANCEL', '申请取消'),
        ('CLOSED', '关闭')
    )
    STATUS_FUTURE_CHOICES = (
        ('ONHOLD', '暂停'),
        ('CANCELLED', '取消'),
    )
    RESULT_CHOICES = (
        ('', '无结果'),
        ('ALLOW', '允许'),
        ('NOT_ALLOW', '不允许'),
        ('CLOSE_ORDER', '关闭订单')
    )
    is_handle = models.BooleanField(u'是否处理', default=False)
    handle_result = models.CharField(u'处理结果', max_length=20, default='', choices=RESULT_CHOICES, null=True,
                                     blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', null=True)
    user_id = models.CharField(u'User ID', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
    order_status_now = models.CharField(u'Status Now', max_length=20, default='0', choices=STATUS_NOW_CHOICES,
                                        null=True,
                                        blank=True, )
    order_status_future = models.CharField(u'Status Future', max_length=20, default='0', choices=STATUS_FUTURE_CHOICES,
                                           null=True, blank=True, )
    reason = models.CharField(u'原因', max_length=4096, default='', blank=True, null=True)
    reply = models.CharField(u'答复', max_length=4096, default='', blank=True, null=True)
    reply_username = models.CharField(u'Reply User Name', max_length=128, default='', blank=True, null=True)


# 更改订单状态的申请
class hold_cancel_request_control:

    def add(self, request, lab_number, order_status_now, order_status_future, reason):
        res = {}
        try:
            cosa = hold_cancel_request()
            cosa.is_handle = False
            cosa.lab_number = lab_number
            logging.debug(lab_number)
            cosa.user_id = request.user.id
            cosa.user_name = request.user.username
            cosa.order_status_now = order_status_now
            cosa.order_status_future = order_status_future
            cosa.reason = reason
            cosa.save()
            logging.debug('保存成功')
            res['code'] = 0
            res['message'] = 'Success'
            res_js = json.dumps(res)
            return HttpResponse(res_js)
        except Exception as e:
            logging.debug('ex:' + str(e))
            res['code'] = -1
            res['message'] = str(e)
            res_js = json.dumps(res)
            return HttpResponse(res_js)


class lab_order_control:
    def change_status(self,data_dict):
        res = {}
        try:
            condition_key = []
            condition_value = []
            for key,value in data_dict.items():
                if key == 'lab_number':
                    continue
                str = key+"=%s"
                condition_key.append(str)
                condition_value.append(value)

            lab_number = data_dict.get("lab_number","")
            if lab_number == '':
                res['code'] = -1
                res['message'] = "lab_number不存在"
                res_js = json.dumps(res)
                return HttpResponse(res_js)

            condition_value.append(lab_number)

            sql = """UPDATE oms_laborder SET """+','.join(condition_key)+""" WHERE lab_number=%s"""
            with connections['default'].cursor() as cursor:
                cursor.execute(sql, tuple(condition_value))

            res['code'] = 0
            res['message'] = "更新成功"
            res_js = json.dumps(res)
            return HttpResponse(res_js)
        except Exception as e:
            res['code'] = -1
            res['message'] = str(e)
            res_js = json.dumps(res)
            return HttpResponse(res_js)
        finally:
            cursor.close()

class CategoryType(Enum):
    Woman = '1' #女款
    Man = '2' #男款
    Child = '3' #儿童款
    WomanSunGlasses = '4' #女款太阳镜
    ManSunGlasses = '5' #男款太阳镜
    ChildSunGlasses = '6' #儿童款太阳镜


class get_workshop_control():
    def get_workshop(self, vd, ws=None):

        if ws:
            return ws

        ws = -1
        if vd == '2' or vd == '4' or vd == '7' or vd == '8':
            ws = 6
        elif vd == '5':
            ws = 5
        elif vd == '6' or vd == '9':
            ws = 6

        return ws


class PgOrderInvoice(BaseType):
    class Meta:
        db_table = 'oms_pgorder_invoice'

    STATUS_CHOICES=(
        ('UNPAID', u'未支付'),
        ('PAID', u'已支付')
    )

    pg_order_entity_id = models.CharField(u'Base Entity', max_length=128, default='', null=True, blank=True)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True)
    inv_amount = models.DecimalField(u'Invoice amount', max_digits=10, decimal_places=2, default=0)
    status = models.CharField(u'Status', max_length=128, default='UNPAID', null=True, choices=STATUS_CHOICES)
    comments = models.CharField(u'Comments', max_length=512, default='', blank=True, null=True)
    inv_type = models.CharField(u'Invoice type', max_length=512, default='', blank=True, null=True)
    ticket_no = models.CharField(u'Order Number', max_length=128, default='', null=True)
    invoice_id = models.CharField(u'invoice id', max_length=128, default='', null=True, blank=True)


class BlackList(BaseType):
    class Meta:
        db_table = 'oms_black_list'

    customer_name = models.CharField(u'Customer Name', max_length=128, default='', null=True)
    firstname = models.CharField(u'Firstname', max_length=128, default="", null=True)
    lastname = models.CharField(u'Lastname', max_length=128, default='', null=True)
    phone = models.CharField(u'Customer Phone', max_length=128, default='', null=True)
    email = models.CharField(u'Customer Email', max_length=128, default='', null=True, blank=True)


class PurchaseOrderRecords(BaseType):
    class Meta:
        db_table = 'oms_purchase_order_records'
    lab_number = models.CharField(u'Fame', max_length=128, default='', blank=True, null=True, unique=True)
    vendor = models.CharField(u'Vendor', max_length=20, default='', blank=True, null=True)
    order_data = models.TextField(u'Order Data', max_length=4000, null=True, blank=True, default='')


class BlueGlasses(BaseType):
    class Meta:
        db_table = 'oms_blue_glasses'
    frame = models.CharField(u'镜架编码', max_length=128, default='', null=True)
