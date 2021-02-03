# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from order_models import *
from django.contrib.auth.models import User
from .order_models import LabOrder


class OrderTracking(models.Model):
    def __str__(self):
        return str(self.id) + ' : ' + self.order_number

    #  Type
    SHIP_DIRECTION_CHOICES = (
        ('US', 'US'),
        ('CN', 'CN'),
    )

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='ORTR', editable=False)  # 订单

    order_number = models.CharField(u'Order Number', max_length=128, null=False, blank=False, default='')
    sku = models.CharField(u'Sku', max_length=128, null=True, blank=True, default='')

    order_date = models.DateTimeField(u'Created Date', null=True, blank=True)
    lab_order_entity = models.IntegerField(u'lab_order_entity', default=0)
    #lab_order_entity = models.ForeignKey(LabOrder, models.SET_NULL,
    #                                     blank=True,
    #                                     null=True,
    #                                     )
    user_entity = models.IntegerField(u'user_entity', default=1)
    #user_entity = models.ForeignKey(User, models.SET_NULL,
    #                                blank=True,
    #                                null=True, )

    username = models.CharField(u'User Name', max_length=128, null=True, blank=True, default='')
    action = models.CharField(u'Action', max_length=128, null=True, blank=True, default='')
    action_value = models.CharField(u'Action Value', max_length=128, null=True, blank=True, default='')
    # print_date = models.DateTimeField(u'打印', null=True, blank=True, default='')
    # frame_outbound = models.DateTimeField(u'镜架出库', null=True, blank=True, default='')
    # add_hardened = models.DateTimeField(u'加硬', null=True, blank=True, default='')
    # coating = models.DateTimeField(u'加膜', null=True, blank=True, default='')
    # tint = models.DateTimeField(u'染色', null=True, blank=True, default='')
    # lens_receive = models.DateTimeField(u'镜片收货', null=True, blank=True, default='')
    # assembling = models.DateTimeField(u'装配', null=True, blank=True, default='')
    # initial_inspection = models.DateTimeField(u'初检', null=True, blank=True, default='')
    # shaping = models.DateTimeField(u'整形', null=True, blank=True, default='')
    # purging = models.DateTimeField(u'清洗', null=True, blank=True, default='')
    # final_inspection = models.DateTimeField(u'终检', null=True, blank=True, default='')
    # order_match = models.DateTimeField(u'订单配对', null=True, blank=True, default='')
    # package = models.DateTimeField(u'包装', null=True, blank=True, default='')
    # shipping = models.DateTimeField(u'发货', null=True, blank=True, default='')
    # estimated_time = models.DateTimeField(u'预计发货时间', null=True, blank=True, default='')
    # final_time = models.DateTimeField(u'实际发货时间', null=True, blank=True, default='')
    remark = models.CharField(u'Remark', max_length=1024, null=True, blank=True, default='')

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    # 是否同步到MRP
    is_sync = models.BooleanField(u'是否同步到MRP', default=0, null=False, blank=False)

    def add_orderTracking(self, order_number, sku, order_date, lab_order_entity, user_entity, username, action,
                          action_value):
        self.order_number = order_number
        self.sku = sku
        self.order_date = order_date
        self.lab_order_entity = lab_order_entity.id
        self.user_entity = user_entity.id
        self.username = username
        self.action = action
        self.action_value = action_value
        self.save()

    def modify_enable(self, order_number):
        ots = OrderTracking.objects.filter(Q(action='ASSEMBLING') | Q(action='LENS_RECEIVE'), order_number=order_number,
                                           is_enabled=True)
        if ots:
            for ot in ots:
                ot.is_enabled = False
                ot.save()
