# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class OrderTrackingReportCS(models.Model):
    def __str__(self):
        return str(self.id) + ' : ' + self.order_number

    CS_STATUS = (
        ('CS_PREPARE', '准备'),
        ('CS_MANUFACTURING', '生产中'),
        ('CS_PACKING', '包装'),
        ('CS_SHIPPED', '已发货'),
        ('CS_ONHOLD', '已暂停'),
        ('CS_CANCELLED', '已取消'),
        ('CS_REDO', '重做'),
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OTRC', editable=False)  # 订单

    pgorder_number = models.CharField(u'PgOrder Number', max_length=128, default='', null=True, blank=True)
    shipping_method = models.CharField(u'Shipping Method', max_length=128, null=True, blank=True, default='')

    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True,
                                    unique=True)  # 该属性必须唯一
    sku = models.CharField(u'Sku', max_length=128, null=True, blank=True, default='')
    order_date = models.DateTimeField(u'Order Date', null=True, blank=True)
    cs_status = models.CharField(u'CS Status', max_length=40, null=True, blank=True, default='CS_PREPARE',
                                 choices=CS_STATUS)
    estimated_time = models.DateTimeField(u'Estimated Time', null=True, blank=True)
    final_time = models.DateTimeField(u'Final Time', null=True, blank=True)
    carriers = models.CharField(u'Carriers', max_length=128, null=True, blank=True, default='')
    shipping_number = models.CharField(u'Shipping Number', max_length=128, null=True, blank=True, default='')
    remark = models.CharField(u'Remark', max_length=4000, null=True, blank=True, default='')

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

    '''添加一个对象'''

    def add_object(self, pgorder_number=None, shipping_method=None, order_number=None, sku=None, order_date=None,
                   cs_status=None, estimated_time=None, final_time=None, carriers=None, shipping_number=None,
                   remark=None):
        self.pgorder_number = pgorder_number
        self.shipping_method = shipping_method
        self.order_number = order_number
        self.sku = sku
        self.order_date = order_date
        self.cs_status = cs_status
        self.estimated_time = estimated_time
        self.final_time = final_time
        self.carriers = carriers
        self.shipping_number = shipping_number
        self.remark = remark
        self.save()
