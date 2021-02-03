# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from base_type_models import *

class SendComment(BaseType):
    type = models.CharField(u'类型', max_length=20, default='SECO', editable=False)
    key = models.CharField(max_length=128,default='',blank=True,null=True)
    value = models.TextField(max_length=4000,blank=True,null=True,default='')
