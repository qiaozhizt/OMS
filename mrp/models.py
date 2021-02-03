# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
# Base Type
from util.base_type import base_type

from oms.models.choices_models import *


class job_base(base_type):
    class Meta:
        abstract = True

    type = models.CharField(u'Type', max_length=20, default='OJOB', editable=False)
    order_number = models.CharField(u'Order Number', max_length=128, default='', null=True, blank=True)
    entity_id = models.CharField(u'Entity ID', max_length=128, default='', null=True, blank=True)
    lab_number = models.CharField(u'Lab Number', max_length=128, default='', null=True, blank=True)
    status = models.CharField(u'Status', max_length=128, default='', null=True)
    frame = models.CharField(u'Frame', max_length=128, default='', null=True, blank=True)
    lens_sku = models.CharField(u'Lens SKU', max_length=128, default='', null=True, blank=True)


class job_tracking(job_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OJTK', editable=False)


class job_archived(job_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OJAR', editable=False)


class job_log(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OJLG', editable=False)
    last_entity_id = models.IntegerField(u'Last Entity ID', default=0)
