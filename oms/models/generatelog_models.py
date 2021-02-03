# -*- coding: utf-8 -*-

from django.db import models
"""
generate pgorder records
"""
class GenerateLog(models.Model):

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='GENL', editable=False)

    last_entity = models.IntegerField(u'Last Entity', null=False, blank=False, default=0)
    current_entity = models.IntegerField(u'Current Entity', null=False, blank=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
