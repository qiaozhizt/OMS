# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.views import namedtuplefetchall
import logging
from django.db import connections
import codecs
from wms.models import inventory_struct_warehouse

'''
根据镜架sku 查找对应图片
'''


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info('sync_localtion start ....')
        try:
            file = "./data/inventory_location.txt"
            with codecs.open(file, 'r', 'utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    localtion, sku = line.split("\t")
                    sku = sku.replace("\n", "").replace("\r", "")
                    if sku == '':
                        continue

                    with connections['default'].cursor() as cursor:
                        sql = """SELECT sku FROM wms_inventory_struct_warehouse where sku='%s' and warehouse_code='W02'""" % sku
                        logging.info(sql)
                        cursor.execute(sql)
                        res = namedtuplefetchall(cursor)
                        logging.info('res len: {0}'.format(len(res)))
                        if len(res) > 0:
                            update_sql = """UPDATE wms_inventory_struct_warehouse SET location=%s WHERE sku=%s and warehouse_code='W02' """
                            cursor.execute(update_sql, (localtion, sku))
            logging.info('end ....')
        except Exception as e:
            logging.exception(e.message)

        logging.critical('sync_localtion end ....')
