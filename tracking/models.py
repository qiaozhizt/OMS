# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models

# Create your models here.
from util.base_type import base_type
from util.response import response_message
import logging


class ai_log(base_type):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'Type', max_length=20, default='OAIL', editable=False)
    object_type = models.CharField(u'Object Type', max_length=128, default='')
    object_entity = models.CharField(u'Object Entity', max_length=128, default='')
    doc_number = models.CharField(u'Document Number', max_length=128, default='')
    action = models.CharField(u'Action', max_length=128, default='', null=True)
    fields = models.CharField(u'Fields', max_length=40, default='', null=True, blank=False)
    origin_value = models.TextField(u'Origin Value', null=True, blank=True, default='')
    new_value = models.TextField(u'New Value', default='', null=True, blank=True)
    error_code = models.CharField(u'错误代码', max_length=20, default='')
    error_message = models.CharField(u'错误信息', max_length=512, default='')
    status = models.CharField(u'Status ', max_length=40, default='')


class ai_log_control:
    def add(self, object_type, object_entity, doc_number, action, fields, origin_value, new_value, error_code,
            error_message, status, comments):
        rm = response_message()
        try:
            log = ai_log()
            log.object_type = object_type
            log.object_entity = object_entity
            log.doc_number = doc_number
            log.action = action
            log.fields = fields
            log.origin_value = origin_value
            log.new_value = new_value
            log.error_code = error_code
            log.error_message = error_message
            log.status = status
            log.comments = comments
            log.save()
            return rm
        except Exception as e:
            logging.debug(str(e))
            rm.capture_execption(e)
        return rm

