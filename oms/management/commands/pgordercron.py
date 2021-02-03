# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.management.base import BaseCommand
from oms.models.order_models import *
from oms.views import namedtuplefetchall
import logging
from django.db import connections
from django.db import transaction
from collections import namedtuple


"""维护pgorder的phone和base_entity字段"""
# class Command(BaseCommand):
#     def handle(self, *args, **options):
#         with connections['pg_mg_query'].cursor() as cursor:
#             logging.debug(sql)
#             cursor.execute(sql)
#             results = namedtuplefetchall(cursor)
#
#             sql_order_list = '''
#                     select t0.entity_id
#                     from sales_order_grid t0
#                     where
#                                             t0.entity_id >= 0
#                     '''
#
#             cursor.execute(sql_order_list)
#             results_order_list = namedtuplefetchall(cursor)
#             for ri in range(len(results_order_list)):
#                 i = results_order_list[ri].entity_id
#
#                 logging.debug(i)
#
#                 logging.debug("")
#                 logging.debug("")
#                 logging.debug("######################################################################")
#                 logging.debug("正在处理Entity ID: %s pgorder ...." % i)
#
#                 """生成pgorder"""
#                 for r in range(len(results)):
#                     po = PgOrder()
#                     if results[r].entity_id == i:
#                         try:
#                             pgorder = po.query_by_id(results[r].increment_id)
#                             pgorder.phone = results[r].telephone
#                             pgorder.base_entity = results[r].entity_id
#                             pgorder.save()
#                         except:
#                             logging.debug("没有pgorder")
#                         break
#
#             logging.debug("-----------------complete-------------------")
#
#         # poc = PgOrderControl()
#         # poc.generate_phone_and_base_entity()
#         logging.debug("------------------------success--------------------------")