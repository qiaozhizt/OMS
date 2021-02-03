# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.models.order_models import *
from oms.views import namedtuplefetchall
import logging
from django.db import connections
from django.db import transaction
from collections import namedtuple
import datetime

from wms.models import inventory_initial, inventory_struct, product_frame

"""维护pgorder的phone和base_entity字段"""


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start ....')
        with open('inventory.csv') as inv_file:
            line = inv_file.readline()
            while line:
                lines = line.split(',')
                sku = lines[0]
                qty = lines[1]
                if sku.find('-') > 0:
                    sku = sku.replace('-', '')

                if int(qty) > 0:
                    prods = product_frame.objects.filter(sku=sku)
                    if len(prods) > 0:
                        prod = prods[0]
                        logging.critical('Product 已更新: %s' % sku)
                    else:
                        prod = product_frame()
                        prod.comments = '系统初始化时自动创建'
                        logging.critical('Product created: %s' % sku)

                    prod.sku = sku
                    prod.user_id = 1
                    prod.user_name = 'System'
                    prod.save()

                    invis = inventory_initial.objects.filter(sku=sku)
                    if len(invis) > 0:
                        invi = invis[0]
                        invi.comments += '\n' + datetime.datetime.now().strftime('%Y-%m-%d|%H:%M:%S') + '系统自动更新'
                    else:
                        invi = inventory_initial()
                        invi.comments = '系统批量自动创建'

                    invi.user_id = 1
                    invi.user_name = 'System'
                    # invi.comments = '系统批量自动创建'
                    invi.sku = sku
                    invi.quantity = decimal.Decimal(qty)
                    invi.save()

                    logging.critical('库存初始化成功')

                    invss = inventory_struct.objects.filter(sku=sku)
                    if len(invss) > 0:
                        invs = invss[0]
                        invs.comments += '\n' + datetime.datetime.now().strftime('%Y-%m-%d|%H:%M:%S') + '系统自动更新'
                    else:
                        invs = inventory_struct()
                        invs.comments = '系统批量自动创建'

                    invs.user_id = 1
                    invs.user_name = 'System'
                    invs.sku = sku
                    invs.quantity += decimal.Decimal(qty)
                    invs.save()

                    logging.critical('库存结构创建成功')

                else:
                    pass
                    # logging.critical('库存小于0, 跳过: %s' % sku)

                line = inv_file.readline()

        logging.critical('所有操作成功结束 ....')
