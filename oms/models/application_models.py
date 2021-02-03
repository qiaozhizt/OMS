# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User
from django.db import transaction
import logging


# Create your models here.
class ObjectType(models.Model):
    def __str__(self):
        return str(self.id) + ':' + self.type + ' -> ' + ':' + self.object_type + ' -> ' + self.description

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='SOBT', editable=False)  # 对象类型描述

    object_type = models.CharField(u'Object Type', max_length=128, default='')
    description = models.CharField(u'Description', max_length=512, default='', null=True, blank=True)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    create_at = models.DateTimeField(auto_now_add=True)
    update_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)


class OperationLog(models.Model):
    def __str__(self):
        return str(self.id) + ':' + self.type

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='SOPL', editable=False)  # 操作日志
    object_type = models.CharField(u'Object Type', max_length=128, default='')
    object_entity = models.CharField(u'Object Entity', max_length=128, default='')
    doc_number = models.CharField(u'Document Number', max_length=512, default='')
    action = models.CharField(u'Action', max_length=128, default='', null=True)
    fields = models.CharField(u'Fields', max_length=40, default='', null=True, blank=False)

    origin_value = models.TextField(u'Origin Value', null=True, blank=True, default='')
    new_value = models.TextField(u'New Value', default='', null=True, blank=True)
    user_entity = models.ForeignKey(User, models.SET_NULL,
                                    blank=True,
                                    null=True, )
    user_id = models.CharField(u'User ID', max_length=128, default='', null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', null=True)

    comments = models.TextField(u'Comments', null=True, blank=True, default='')
    content = models.TextField(u'Content', null=True, blank=True, default='')
    is_async = models.BooleanField(u'Is Async', default=False)

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    sequence = models.IntegerField(u'Sequence', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_enabled = models.BooleanField(u'Is Enabled', default=True)

    def query_specific_log(self, object_entity, new_value):
        ols = OperationLog.objects.filter(object_entity=object_entity, new_value=new_value)[:1]
        if ols:
            return ols[0].origin_value
        else:
            return False

    # 添加操作记录
    def log(self, type, id, action_value, field, user, origin_value=None, new_value=None,
            content=None,
            comments=None
            ):

        self.object_type = type
        self.object_entity = id
        self.action = action_value
        self.fields = field
        self.origin_value = origin_value
        self.new_value = new_value
        self.user_entity = user
        self.user_name = user.username
        self.content = content
        self.comments = comments

        self.save()
