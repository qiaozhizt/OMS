# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.db import transaction
# from .dict_models import *
# from .product_models import *

import time
import datetime
import logging

from django.utils import timezone
from django.core import serializers
# from holiday_setting_models import HolidaySetting

from django.forms import ModelForm
from api.controllers.tracking_controllers import tracking_lab_order_controller
from util.base_type import base_type
from util.response import response_message
from oms.controllers.lab_order_controller import lab_order_controller


class documents_base(base_type):
    class Meta:
        abstract = True

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='DOCB', editable=False)

    lab_order_entity = models.CharField(u'单号', max_length=128, default='', null=True)
    lab_number = models.CharField(u'单号', max_length=128, default='', null=True)
    status = models.CharField(u'状态', max_length=128, null=True, blank=True, default='')
    base_entity = models.CharField(u'基础单据', max_length=128, default='', null=True)


class assembled(documents_base):
    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    type = models.CharField(u'类型', max_length=20, default='OWCA', editable=False)
    comments = models.TextField(u'备注', max_length=512, default='', null=True, blank=True)


class assembled_control:
    def add(self,
            request,
            lab_order_entity,
            ):
        rm = response_message()
        rm.message = '此操作已成功'

        try:
            logging.debug('开始进入 ...')
            with transaction.atomic():
                loc = lab_order_controller()
                lbos = loc.get_by_entity(lab_order_entity)

                lbo = None
                if len(lbos) > 0:
                    lbo = lbos[0]

                if not lbo == None:
                    objs = assembled.objects.all().order_by('-id')[:1]
                    if len(objs) > 0:
                        ob = objs[0]
                        if ob.lab_number == lbo.lab_number:
                            rm.code = -3
                            rm.message = '疑似重复操作'
                            return rm

                    if not lbo.status == 'ASSEMBLING':

                        rm.code = -4
                        rm.message = '只有订单处于待装配的状态时才可以执行装配完成:{%s}' % lbo.get_status_display()
                        return rm

                    rg = assembled()
                    rg.lab_order_entity = lbo.id
                    rg.lab_number = lbo.lab_number

                    rg.user_id = request.user.id
                    rg.user_name = request.user.username

                    rg.save()

                    lbo.status = 'ASSEMBLED'
                    lbo.save()

                    tloc = tracking_lab_order_controller()
                    tloc.tracking(lbo, request.user, "ASSEMBLED", "装配完成")

                    rm.obj = rg

                else:
                    rm.code = -4
                    rm.message = '订单未找到'
                    return rm

        except Exception as e:
            logging.debug(e.message)
            rm.capture_execption(e)

        return rm


class assembling_control:
    def get_items(self, params):
        status = params.get('status', 'ASSEMBLING')
        vendor = params.get('vendor', '')
        vendor_where = 'and vendor="%s"' % vendor
        if vendor == 'all':
            vendor_where = ''
        items = []
        from django.db import connections
        from util.db_helper import *
        with connections["pg_oms_query"].cursor() as cursor:
            sql = '''
            SELECT * FROM report_assembling_lab_orders
            WHERE status="%s" %s
            ''' % (status, vendor_where,)
            logging.debug(sql)
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)

            for r in range(len(results)):
                items.append(results[r])

        return items


class Assembler(models.Model):
    class Meta:
        db_table = 'workshop_assembler'

    # 属性清单 :: 在所有对象中，必须包含 [type, sequence, is_enabled]
    is_enabled = models.BooleanField(u'Is Enabled', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    user_code = models.CharField(u'User Code', max_length=128, default='', blank=True, null=True)
    user_name = models.CharField(u'User Name', max_length=128, default='', blank=True, null=True)
    department = models.CharField(u'Department', max_length=128, default='', blank=True, null=True)