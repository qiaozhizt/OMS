# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.utils import timezone

from django.core.management.base import BaseCommand
from oms.views import *
from oms.const import *
import logging
import datetime
from django.db.models import Q

from django.http import HttpRequest
from oms.controllers.order_controller import *
from oms.models.post_models import Prescription
from oms.models.product_models import PgProduct

from oms.controllers.lab_order_controller import lab_order_controller
from pg_oms.settings import *
from wms.models import lens_extend
from vendor.models import lens
from vendor.contollers import distribute_controller


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start distribute lab orders ....')

        AI_CODE = 'AI_90312'
        AI_CODE = 'AI_200316'
        '''
        可控制的规则参数：
        1.所有镜片的优先级
        2.各VD单日累计数量限制
        3.特定VD的度数范围限制-比如VD6的正负300 
        
        规则代码：
        1.如果是车房片，如果是车房单光，则优先进入库存片规则
        2.否则，初选供应商为vd5和vd4，在镜片中根据优先级确认具体供应商
        3.如果是库存片，如果是1.56折射率以外的镜片，按照库存片规则
        4.如果是1.56或1.50折射率，则按照度数范围，近视和老花300度以下的镜片，并且无染色抗蓝功能性要求，则分配给vd6
        5.如果超出此度数范围，按照近视和老花单独确定具体的sku，并且不区分是否大直径，直到我们的直径计算很精确，默认全部分给vd2
        6.如果1天中分配给vd2的累计数量超过100，则分配给vd3
        7.如果订单中任意一只光度度数是.25或.75，则自动升级为MR-8
        8.根据Lab Order中的Lens Sku在指定的供应商中，通过优先级确定供应商及Lens Sku。
        9.优先级分为10级，优先级相同的，自动取供应商的优先级。
        10.如果出现同一供应商的镜片优先级相同，则取Sequence字段。
        11.无框的镜架如果选择了1.56折射率的镜片，则自动升级为1.59PC
        12.VD1000_FRAME_LIST列表中的镜架，平光的，分配到VD1000
        '''

        index = 0

        try:
            dlc = distribute_controller()

            today = timezone.now().date()

            # Lab Order List:
            # 只对新订单做分配
            lbos = LabOrder.objects.filter(is_enabled=True, is_ai_checked=False) \
                .filter(
                Q(status=None) |
                Q(status=''))

            # logging.critical(lbos.query)

            msg = '(%s):%s: %s'

            for lbo in lbos:
                logging.critical(msg % (str(index), lbo.lab_number, lbo.status))
                entity_id = lbo.id
                LabOrder.objects.filter(id=entity_id).update(is_ai_checked=True)
                comments = ''
                index += 1

                parameters = {}
                dlc.distribute_vendor(lbo, parameters)

        except Exception as e:
            logging.critical(str(e))

        logging.critical('distribute lab orders completed ....')

    def __determine_prescription(self, lbo):
        pass
