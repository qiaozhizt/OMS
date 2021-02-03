# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

class Shipment(models.Model):
    def __str__(self):
        return str(self.id) + ':' + self.type

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='SHIP', editable=False)  # 操作日志

    CARRIER_NAME = (
        ('UPS', 'UPS'),
        ('EMS', '邮政(EMS)'),
        ('SF', '顺丰'),

    )

    carrierNumber = models.CharField(u'单号', max_length=30, unique=True)
    remark = models.CharField(u'备注', max_length=1000, null=True, blank=True)
    carrier = models.CharField(u'承运商', max_length=40, default='UPS', choices=CARRIER_NAME)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)