# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class LabOrderStatusVerifyException(Exception):
    '''
     Custom exception types
     '''

    def __init__(self, parameter, para_value):
        err = 'The Lab Order "{0}" current status is :"{1}" can not processing . Lab Order 当前状态不允许执行此操作.'.format(parameter, para_value)

        Exception.__init__(self, err)
        self.parameter = parameter
        self.para_value = para_value


class LabOrderDuplicationException(Exception):
    '''
     Custom exception types
     '''

    def __init__(self, parameter, para_value=None):
        err = 'The Lab Order "{0}" is duplication . 订单号重复.'.format(parameter)

        Exception.__init__(self, err)
        self.parameter = parameter
        self.para_value = para_value
