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


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start distribute lab orders ....')

        AI_CODE = 'AI_81022'
        AI_CODE = 'AI_81112'
        AI_CODE = 'AI_90117'
        AI_CODE = 'AI_90219'
        '''
         81022:规则
               0.准备条件:所有新订单[None/'']&未分配状态[vendor=0]
               1.VD1,所有库存片/1.56白片[不包含偏光/抗蓝/膜变/染色]/非加急
               2.除VD1之外的符合条件的订单,暂时默认分配给VD3
        '''

        '''
        hotfixes/hotfix.1.0.811122
        
        规则调整-81112
        1.原分给vd3的部分，除染色/变色和1.74折射率的，仍分给VD3做成镜；
        2.除此之外的部分，全部分到VD2采购镜片。
        '''

        '''
        hotfixes/hotfix.1.0.81113
        
        规则调整-81113
        1.如果单日订单分配到VD1的，超过100单时自动转到VD2
        2.如果计划转给VD1的订单SPH超过600，自动转单给VD3
        '''

        index = 0

        try:
            today = timezone.now().date()

            vd1s = LabOrder.objects.filter(is_enabled=True, vendor='1').filter(
                ~Q(status='CANCELLED')).filter(
                create_at__year=today.year,
                create_at__month=today.month,
                create_at__day=today.day
            )

            logging.critical(vd1s.query)

            vd1_count = vd1s.count()

            # Lab Order List:
            lbos = LabOrder.objects.filter(is_enabled=True, is_ai_checked=False) \
                .filter(
                Q(status=None) |
                Q(status=''))

            logging.critical(lbos.query)

            msg = '(%s):%s: %s'

            approved_pgos = []

            '''
             抗蓝单光片
            '''
            kds = [
                'KD50L',
                'KD56L',
                'KD59L',
                'KD61L',
                'KD67L',
                'KDB56L-H',
                'KDB56L-C',
                'KDB59L-C',
                'KDB59L-H',
                'KDB61L-C',
                'KDB61L-H',
                'KDB67L-C',
                'KDB67L-H'
            ]

            for lbo in lbos:
                logging.critical(msg % (str(index), lbo.lab_number, lbo.status))
                lbo.is_ai_checked = True
                lbo.save()
                index += 1
                is_can_auto = True

                # 如果订单的vendor不等于0，则不再进行二次分配
                if not int(lbo.vendor) == 0:
                    comments = '|疑似重做订单,当前Vendor[%s]AI不作二次分配' % lbo.vendor
                    comments += '|自动分配-程序代码[%s]' % AI_CODE
                    lbo.comments_inner += comments
                    lbo.save()
                    continue

                lens = LabProduct.objects.get(sku=lbo.lens_sku)

                if lens.is_rx_lab:
                    # 按计划镜片
                    # 所有车房单光 自动分配给VD2
                    if '车房单光' in lens.name:
                        lbo.vendor = 2
                        lbo.comments_inner += '|车房单光-自动分配-程序代码[%s]' % AI_CODE
                    continue
                else:
                    if float(lbo.od_add) > 0.00 or float(lbo.os_add) > 0.00:
                        lbo.comments_inner += '|库存片包含ADD，需人工受理-[%s]' % AI_CODE
                        lbo.is_ai_checked = True
                        lbo.save()
                        continue

                    if float(lbo.od_prism) > 0.00 or float(lbo.os_prism) > 0.00:
                        lbo.comments_inner += '|库存片包含PRISM，需人工受理-[%s]' % AI_CODE
                        lbo.is_ai_checked = True
                        lbo.save()
                        continue

                    if abs(float(lbo.od_cyl)) > 2.00 or abs(float(lbo.os_prism)) > 2.00:
                        lbo.comments_inner += '|库存片散光超过200度，需人工受理-[%s]' % AI_CODE
                        lbo.is_ai_checked = True
                        lbo.save()
                        continue

                    if lens.index == '1.56' \
                            and (lbo.coating_sku == None or lbo.coating_sku == '') \
                            and (lbo.tint_sku == None or lbo.tint_sku == '') \
                            and (not lbo.lens_sku == 'KD56L') \
                            and (not lbo.lens_sku == 'KDB56L-H' and not lbo.lens_sku == 'KDB56L-C')\
                            and (not lbo.lens_sku == 'KDB56-C' and not lbo.lens_sku == 'KDB56-H'): # \
                            # and not lbo.ship_direction == 'EXPRESS':

                        # 如果是小于300度的近视或老花 分配给VD6
                        # 2019.02.19 by guof.
                        if abs(float(lbo.od_sph)) <= 3 and abs(float(lbo.os_sph)) <=3:
                            lbo.vendor = 6
                            lbo.comments_inner += '|自动分配-光度符合VD6范围-程序代码[%s]' % AI_CODE
                        # 如果右眼或左眼的光度>600度，自动分给VD3
                        elif abs(float(lbo.od_sph)) > 6 or abs(float(lbo.os_sph)) > 6:
                            lbo.vendor = 3
                            lbo.comments_inner += '|自动分配-光度超范围-程序代码[%s]' % AI_CODE
                        elif vd1_count > settings.VD1_DAILY_LIMIT:  # 如果当日订单超过100，自动调整
                            lbo.vendor = 2
                            comments = '|[%d/%d]' % (vd1_count, settings.VD1_DAILY_LIMIT)
                            lbo.comments_inner += comments
                            lbo.comments_inner += '|自动分配-单日订单超限-程序代码[%s]' % AI_CODE
                        elif float(lbo.od_sph) <= 0:
                            lbo.vendor = 2
                            lbo.comments_inner += '|近视-自动分配-程序代码[%s]' % AI_CODE
                        # 老花的也分给VD2，避免老花额外收费 2019.01.12 by guofu.
                        else:
                            lbo.vendor = 2
                            lbo.comments_inner += '|老光-自动分配-程序代码[%s]' % AI_CODE
                        # else:
                        #     lbo.vendor = 1
                        #     lbo.comments_inner += '|自动分配-程序代码[%s]' % AI_CODE
                        lbo.save()
                    else:
                        if lens.index == '1.74' or (not lbo.coating_sku == None and not lbo.coating_sku == '') \
                                or (not lbo.tint_sku == None and not lbo.tint_sku == ''):
                            lbo.vendor = 3
                            lbo.comments_inner += '|自动分配-程序代码[%s]' % AI_CODE
                            lbo.save()
                        else:
                            lbo.vendor = 2
                            lbo.comments_inner += '|自动分配-程序代码[%s]' % AI_CODE
                            lbo.save()

        except Exception as e:
            logging.critical(e.message)

        logging.critical('distribute lab orders completed ....')
