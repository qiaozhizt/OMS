# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.views import namedtuplefetchall
import logging
from django.db import connections
import codecs
#from oms.controllers.pg_order_controller import pg_order_controller
from api.controllers.pgorder_frame_controllers import pgorder_frame_controller


'''
根据镜架sku 查找对应图片
'''


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info('start ....')
        try:
            sku_image = {}
            file = "./data/product_list.txt"
            with codecs.open(file, 'r', 'utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    sku, image, thumbnail = line.split("\t")
                    if len(sku) < 7:
                        continue
                    else:
                        poc = pgorder_frame_controller()
                        res_rm = poc.get_lab_frame({"pg_frame": sku})
                        if not sku_image.has_key(res_rm.obj['lab_frame']):
                            sku_image[sku] = image

            with connections['default'].cursor() as cursor:
                sql = '''SELECT sku FROM wms_product_frame'''
                logging.info(sql)
                cursor.execute(sql)
                for item in namedtuplefetchall(cursor):
                    update_sql = """UPDATE wms_product_frame SET image=%s,thumbnail=%s WHERE sku=%s"""
                    cursor.execute(update_sql, (sku_image.get(item.sku, ''), sku_image.get(item.sku, ''), item.sku))

            logging.info('end ....')
        except Exception as e:
            logging.exception(e.message)

        logging.critical('所有操作成功结束 ....')
