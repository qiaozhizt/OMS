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
import csv

from wms.models import inventory_initial, inventory_struct, product_frame

"""维护pgorder的phone和base_entity字段"""

'''
统计在网站的产品的销量
'''


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start ....')

        try:

            sku_sales_qty_list = []

            sku_sales_qty = {}

            with connections['pg_mg_query'].cursor() as cursor:
                sql = '''
                select 
                    RIGHT(t1.sku,7) as lab_sku
                    ,sum(t1.qty_ordered) as qty
                    ,t1.product_type
                    ,t0.status
                    from sales_order t0
                    left join sales_order_item t1 on t0.entity_id=t1.order_id
                    group by lab_sku
                    having t1.product_type='configurable'
                    -- and (t0.status='processing' or t0.status='complete')
                    order by lab_sku
                '''

                logging.info(sql)
                cursor.execute(sql)

                results = namedtuplefetchall(cursor)
                for res in results:
                    sku_sales_qty = {}
                    sku_sales_qty['sku'] = res.lab_sku
                    sku_sales_qty['saled_qty'] = int(res.qty)

                    inss = inventory_struct.objects.filter(sku=res.lab_sku)
                    if len(inss) > 0:
                        ins = inss[0]
                        sku_sales_qty['lab_qty'] = int(ins.quantity)
                    else:
                        sku_sales_qty['lab_qty'] = int('0')
                    sku_sales_qty_list.append(sku_sales_qty)

                    logging.critical(sku_sales_qty)

                    out = open('out_qty.csv', 'a')
                    csv_write = csv.writer(out)
                    csv_write.writerow([sku_sales_qty['sku'], sku_sales_qty['saled_qty'], sku_sales_qty['lab_qty']])

        except Exception as e:
            logging.exception(e.message)

        logging.critical('所有操作成功结束 ....')
