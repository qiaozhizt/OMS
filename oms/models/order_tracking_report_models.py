# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from order_models import *

class OrderTrackingReport(models.Model):
    def __str__(self):
        return str(self.id) + ' : ' + self.lab_order_number


    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OTRE', editable=False)  # 订单

    lab_order_number = models.CharField(u'单号', max_length=128, null=False, blank=False, unique=True)
    sku = models.CharField(u'Sku', max_length=128, null=True, blank=True, default='')

    order_date = models.DateTimeField(u'下单日期', null=True, blank=True)

    lab_order_entity = models.ForeignKey(LabOrder, models.SET_NULL,
                                         blank=True,
                                         null=True,
                                         )

    print_date = models.DateTimeField(u'打印', null=True, blank=True)
    frame_outbound = models.DateTimeField(u'镜架出库', null=True, blank=True)
    tint = models.DateTimeField(u'染色', null=True, blank=True)
    rx_lab = models.DateTimeField(u'车房', null=True, blank=True)
    add_hardened = models.DateTimeField(u'加硬', null=True, blank=True)
    coating = models.DateTimeField(u'加膜', null=True, blank=True)

    lens_receive = models.DateTimeField(u'镜片收货', null=True, blank=True)
    initial_inspection = models.DateTimeField(u'初检', null=True, blank=True)
    assembling = models.DateTimeField(u'装配', null=True, blank=True)

    shaping = models.DateTimeField(u'整形', null=True, blank=True)
    final_inspection = models.DateTimeField(u'终检', null=True, blank=True)
    purging = models.DateTimeField(u'清洗', null=True, blank=True)

    order_match = models.DateTimeField(u'订单配对', null=True, blank=True)
    package = models.DateTimeField(u'包装', null=True, blank=True)
    shipping = models.DateTimeField(u'发货', null=True, blank=True)
    carriers = models.CharField(u'承运商', max_length=128, null=True, blank=True)
    shipping_number = models.CharField(u'运单号', max_length=128, null=True, blank=True)
    estimated_time = models.DateTimeField(u'预计发货时间', null=True, blank=True)
    final_time = models.DateTimeField(u'实际发货时间', null=True, blank=True)
    remark = models.CharField(u'备注', max_length=40, null=True, blank=True, default='')

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

