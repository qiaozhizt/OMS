# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


# Create your models here.
class ProductType(models.Model):
    def __str__(self):
        return str(self.id)+ ' -> '+self.code+':'+self.name

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='ODPT', editable=False)  # 产品类型

    code = models.CharField(u'Code', max_length=128, default='', null=True, unique=True)  # 该属性必须唯一
    name = models.CharField(u'Name', max_length=512, default='', null=True)
    description = models.CharField(u'Description', max_length=512, default='', null=True, blank=True)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
