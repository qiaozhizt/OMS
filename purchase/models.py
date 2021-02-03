# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction

import logging
import datetime

from util.response import response_message
from util.base_type import base_type

from oms.models.order_models import PgOrder, LabOrder
from oms.controllers.lab_order_controller import lab_order_controller
from qc.models import lens_registration
from oms.models.glasses_models import received_glasses
from django.utils import timezone


# Create your models here.

# 当前Model用到的CHOICE
class choices:
    STATEMENT_STATUS_CHOICES = (
        ('NEW', 'New'),
        ('DRAFT', 'Draft'),
        ('PROCESSING', 'Processing'),
        ('APPROVED', 'Approved'),
        ('COMPLETE', 'Complete'),
    )


# 单据的基类
class documents_base(base_type):
    class Meta:
        abstract = True

    DOC_TYPE_CHOICES = (
        ('GENERAL', '一般类型'),
    )

    doc_type = models.CharField(u'Doc Type', max_length=20, default='AUTO',
                                choices=DOC_TYPE_CHOICES)
    doc_number = models.CharField(u'Doc Number', max_length=40,
                                  default='', null=True, blank=True)
    status = models.CharField(u'状态', max_length=40, default='', blank=True,
                              choices=choices.STATEMENT_STATUS_CHOICES)
    base_entity = models.CharField(u'Base Entity', max_length=128, default='', null=True)


#
class statement_lab_order_lens_daily(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='SLOD', editable=False)

    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, unique=True)

    vendor = models.CharField(u'VD', max_length=128, null=True, blank=True, default='0',
                              choices=LabOrder.VENDOR_CHOICES)
    workshop = models.CharField(u'Work Shop', max_length=128, null=True, blank=True, default='0',
                                choices=LabOrder.WORKSHOP_CHOICES)


class statement_lab_order_lens_daily_line(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='SLOL', editable=False)

    parent = models.ForeignKey(statement_lab_order_lens_daily, models.CASCADE,
                               blank=True,
                               null=True, )

    pg_order_entity_id = models.CharField(u'Pg Order Entity', max_length=128, default='', null=True)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True)
    lab_order_entity_id = models.CharField(u'Lab Order Entity', max_length=128, default='', null=True)
    lab_number = models.CharField(u'Lab Order Number', max_length=128, default='', null=True)
    order_date = models.DateField(u'订单日期', null=True, blank=True)

    frame = models.CharField(u'镜架编码', max_length=128, default='', null=True)
    name = models.CharField(u'镜架', max_length=512, default='', null=True, blank=True)
    quantity = models.IntegerField(u'Quantity', default=1)

    lens_sku = models.CharField(u'Lens Sku', max_length=128, default='', null=True)
    lens_name = models.CharField(u'Lens Name', max_length=512, default='', null=True, blank=True)

    coating_sku = models.CharField(u'Coating Sku', max_length=128, default='', null=True, blank=True)
    coating_name = models.CharField(u'Coating Name', max_length=512, default='', null=True, blank=True)

    tint_sku = models.CharField(u'Tint Sku', max_length=128, default='', null=True, blank=True)
    tint_name = models.CharField(u'Tint Name', max_length=512, default='', null=True, blank=True)

    pal_design_sku = models.CharField(u'PAL Design Sku', max_length=128, default='', null=True, blank=True)
    pal_design_name = models.CharField(u'PAL Design Name', max_length=512, default='', null=True, blank=True)

    vendor = models.CharField(u'VD', max_length=128, null=True, blank=True, default='0',
                              choices=LabOrder.VENDOR_CHOICES)
    workshop = models.CharField(u'Work Shop', max_length=128, null=True, blank=True, default='0',
                                choices=LabOrder.WORKSHOP_CHOICES)


class statement_lab_order_daily_control:
    def get_statment_list(self, request):
        rm = response_message()
        lab_number = request.GET.get('lab_number', '')
        try:
            if not lab_number == '':
                objs = []
                loc = lab_order_controller()
                objs = loc.get_by_entity(lab_number)
                lab_number = objs[0].lab_number
            doc_type = request.GET.get('doc_type', '')
            logging.debug('type' + doc_type)
            if doc_type == 'LENS':
                vendor = request.GET.get('filter', '')
                logging.debug('len' + lab_number)
                year = request.GET.get('year', '')
                month = request.GET.get('month', '')
                day = request.GET.get('day', '')
                if lab_number == '':
                    today = timezone.now().date()

                    if year == '':
                        year = today.year

                    if month == '':
                        month = today.month

                    if day == '':
                        day = today.day

                    year = int(year)
                    month = int(month)
                    day = int(day)

                    if day <> '':
                        day = datetime.date(year, month, day)
                        logging.debug(day)
                        day2 = day + datetime.timedelta(days=1)
                        logging.debug(day2)

                        lrs = lens_registration.objects.filter(created_at__range=(day, day2),
                                                               laborder_entity__vendor=vendor)

                        logging.critical(lrs.query)

                        # logging.debug(lrs.query)

                        # for lr in lrs:
                        #     logging.debug(lr.id)
                    rm.obj = lrs
                else:
                    lrs = lens_registration.objects.filter(lab_number=lab_number)
                    rm.obj = lrs
            else:
                list = []
                rgs = None
                logging.debug(lab_number)
                workshop = request.GET.get('workshop', '')
                year = request.GET.get('year', '')
                month = request.GET.get('month', '')
                day = request.GET.get('day', '')
                if lab_number == '':
                    today = timezone.now().date()

                    if year == '':
                        year = today.year

                    if month == '':
                        month = today.month

                    if day == '':
                        day = today.day

                    year = int(year)
                    month = int(month)
                    day = int(day)

                    if day <> '':
                        day = datetime.date(year, month, day)
                        logging.debug(day)
                        day2 = day + datetime.timedelta(days=1)
                        logging.debug(day2)

                        rgs = received_glasses.objects.filter(created_at__range=(day, day2))

                        for rg in rgs:
                            lbo = LabOrder.objects.get(id=rg.lab_order_entity)
                            ln_rg = received_glasses.objects.filter(created_at__lt=day, lab_number=rg.lab_number)
                            logging.debug(ln_rg.count())
                            if lbo.workshop == workshop and not ln_rg.count():
                                rg.laborder_entity = lbo
                                list.append(rg)

                        logging.debug(rgs.query)
                else:
                    rgs = received_glasses.objects.filter(lab_number=lab_number)
                    logging.debug(rgs.count())
                    for rg in rgs:
                        lbo = LabOrder.objects.get(id=rg.lab_order_entity)
                        rg.laborder_entity = lbo
                        list.append(rg)

                rm.obj = list

            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.critical(e)
            return rm

    def get_statment_month_list(self, request):
        rm = response_message()
        try:
            doc_type = request.GET.get('doc_type', '')
            if doc_type == 'LENS':
                vendor = request.GET.get('filter', '')
                begin_date = request.GET.get('begindate', '')
                end_date = request.GET.get('enddate', '')
                lrs = lens_registration.objects.filter(created_at__range=(begin_date, end_date),
                                                       laborder_entity__vendor=vendor)
                logging.critical(lrs.query)
                rm.obj = lrs
            else:
                workshop = request.GET.get('workshop', '')
                begin_date = request.GET.get('begindate', '')
                end_date = request.GET.get('enddate', '')
                rgs = received_glasses.objects.filter(created_at__range=(begin_date, end_date))
                logging.debug(rgs.query)
                list = []
                for rg in rgs:
                    lbo = LabOrder.objects.get(id=rg.lab_order_entity)
                    if lbo.workshop == workshop:
                        rg.laborder_entity = lbo
                        list.append(rg)
                rm.obj = list
            return rm
        except Exception as e:
            rm.capture_execption(e)
            logging.critical(e.message)
            return rm


class PurchaseOrderChangeLog(base_type):
    class Meta:
        db_table = 'purchase_order_change_log'

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='POCL', editable=False)

    base_type = models.CharField(u'基础类型', max_length=20, default='', null=True)
    base_entity = models.CharField(u'基础单据实体', max_length=128, default='', null=True)
    base_request_notes_id =  models.CharField(u'基础单据实体', max_length=128, default='', null=True)

    origin_vendor = models.CharField(u'原供应商ID', max_length=128, default='', null=True)
    vendor = models.CharField(u'新供应商ID', max_length=128, default='', null=True)

    lab_order_entity = models.CharField(u'工厂订单实体', max_length=128, default='', null=True)
    lab_number = models.CharField(u'工厂订单编号', max_length=128, default='', null=True)
    status = models.CharField(u'状态', max_length=128, default='', null=True)
    frame = models.CharField(u'镜架编码', max_length=128, default='', null=True)
    lens_sku = models.CharField(u'计划镜片编码', max_length=128, default='', null=True)
    lens_name = models.CharField(u'计划镜片名称', max_length=128, default='', null=True)
