# -*- coding: utf-8 -*-
import logging
import time
import codecs
from util.response import response_message
from django.core.management.base import BaseCommand
from wms.models import inventory_struct
from util.db_helper import *
from django.db import connections
from oms.models.order_models import LabOrder, PgOrder, PgOrderItem
from pg_oms import settings
#from oms.controllers.pg_order_controller import pg_order_controller
from  api.controllers.pgorder_frame_controllers import pgorder_frame_controller

class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('---')
        rm = response_message()
        try:
            logging.info("calculation_reserve_quantity start")
            inventory_struct.objects.all().update(reserve_quantity=0)
            sql = """SELECT i.frame as frame, 
                            SUM(i.quantity) AS quantity 
                               FROM oms_pgorder AS p 
                                 LEFT JOIN oms_pgorderitem AS i 
                                 ON p.id = i.pg_order_entity_id 
                               WHERE p.is_inlab=FALSE                     
                                    AND p.status <> 'closed'
                                    AND p.status <> 'canceled' GROUP BY i.frame
                        """
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                items = namedtuplefetchall(cursor)
                for item in items:
                    try:
                        #frame = item.frame[1:8]
                        poc = pgorder_frame_controller()
                        res_rm = poc.get_lab_frame({"pg_frame": item.frame})
                        iis = inventory_struct.objects.get(sku=res_rm.obj['lab_frame'])
                        qty = iis.reserve_quantity + item.quantity
                        iis.reserve_quantity = qty
                        iis.save()
                    except Exception as e:
                        pass

                lab_sql = """SELECT frame, SUM(quantity) AS quantity FROM oms_laborder  WHERE (`status` in ('', NULL, 'REQUEST_NOTES') OR (`status`='ONHOLD' AND current_status in ('', NULL, 'REQUEST_NOTES'))) GROUP BY frame"""
                cursor.execute(lab_sql)
                laborders = namedtuplefetchall(cursor)
                for item in laborders:
                    try:
                        iis = inventory_struct.objects.get(sku=item.frame)
                        qty = iis.reserve_quantity + item.quantity
                        iis.reserve_quantity = qty
                        iis.save()
                    except Exception as e:
                        pass
            logging.info("calculation_reserve_quantity end")
        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
