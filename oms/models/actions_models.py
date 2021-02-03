# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class Action(models.Model):

    def __str__(self):
        return str(self.id) + ' : ' + self.key

    type = models.CharField(u'Type', max_length=20, default='OACS', editable=False)  # 对象类型描述

    key = models.CharField(u'Key',max_length=128, null=True,blank=True, default='')
    value = models.CharField(u'Value',max_length=128, null=True, blank=True, default='')
    object_type = models.CharField(u'Object Type', max_length=40, null=True, blank=True, default='')
    description = models.CharField(u'Description', max_length=512, null=True, blank=True, default='')
    help = models.TextField(u'Help', max_length=4000, null=True, blank=True, default='')
    group = models.IntegerField(u'Group', default=0)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

    def query_actions(self,object_type,group):
        queryset = Action.objects.filter(object_type=object_type, group=group,is_enabled=True).values('key', 'value').order_by('sequence')
        return queryset

