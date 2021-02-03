# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

from django.core.management.base import BaseCommand
from oms.views import *
from oms.const import *
import logging
import datetime
from django.http import HttpRequest
from oms.controllers.order_controller import *


class Command(BaseCommand):
    def handle(self, *args, **options):

        poc = PgOrderController()

        logging.critical("Preparing generate PgOrder & Items ....")

        max_current_entity = generatelogmax()  # 获取当前已经生成到的订单entity_id
        logging.critical("Last Order Entity is: %s" % max_current_entity)

        set_time = set_date()  # 获取 limit_hour 前时间

        logging.critical("UTC Time: %s" % datetime.datetime.utcnow())

        logging.critical("Set Date: %s" % set_date)

        entity_list = entity_id_list()  # 获取entity_id list

        if entity_list:
            with connections['pg_mg_query'].cursor() as cursor:
                sql = const.sql_generate_pg_orders + const.sql_generate_pg_orders_all
                logging.critical(sql % max_current_entity)
                cursor.execute(sql, [max_current_entity])
                results = namedtuplefetchall(cursor)
                current_entity_id = max_current_entity
                if results:
                    try:
                        with transaction.atomic():
                            for i in range(len(entity_list)):
                                for r in range(len(results)):
                                    # logging.critical("result.entity_id={0},entity_list.entity_id={1}".format(results[r].entity_id,entity_list[i].entity_id))
                                    if results[r].entity_id == entity_list[i].entity_id:
                                        resulte = results[r]
                                        logging.critical("current order_number: %s" % resulte.increment_id)
                                        '''生成pgorder'''
                                        current_entity_id = resulte.entity_id

                                        logging.critical("begin generate pgorder ....")
                                        po, flag = poc.gen_pgorder(resulte)  # 生成pgorder 并返回该对象和flag值（True,False）

                                        break

                                if flag:
                                    relatelist = []
                                    # nonelist = []
                                    for j in range(len(results)):
                                        if entity_list[i].entity_id == results[j].entity_id:
                                            relatelist.append(results[j])

                                    """生成pgorderitem"""
                                    logging.critical("begin generate pgorderitem ....")
                                    poc.gen_pgorderitem(relatelist, po)

                            generatelog = GenerateLog()
                            generatelog.last_entity = max_current_entity
                            generatelog.current_entity = current_entity_id
                            generatelog.save()

                            """增加预留数量"""
                            from wms.models import inventory_struct_contoller
                            isc = inventory_struct_contoller()
                            isc.add_reserver_qty_po(po)

                            logging.critical("Successfully generated pgorder !")
                    except Exception as e:
                        logging.critical("When generating order arise Errors: %s" % e)
                else:
                    logging.critical("There is no PgOrders can be generated !")


        else:
            logging.critical("There is no PgOrders can be generated !")
