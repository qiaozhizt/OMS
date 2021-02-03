# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import connections
from django.db import transaction

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

from django.db import connections, transaction


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate lab orders ....')

        try:
            from api.controllers.tracking_controllers import tracking_lab_order_controller
            from util.time_delta import dateDiffInHours
            sql = '''
            DROP TABLE IF EXISTS report_assembling_lab_orders;
            '''

            with connections['default'].cursor() as cursor:
                cursor.execute(sql)

            sql = '''
                CREATE TABLE report_assembling_lab_orders
                (
                SELECT 
                t0.lab_number
                ,t0.create_at 
                ,t0.status
                ,t0.vendor
                ,t0.workshop
                ,t0.frame
                ,t0.quantity
                ,t0.act_lens_sku
                ,t0.act_lens_name
                ,t0.order_date
                ,CONVERT_TZ(purchase.created_at,@@session.time_zone,'+8:00') AS get_purchase_date
                ,TIMESTAMPDIFF(HOUR,purchase.created_at,NOW()) AS hours_of_purchase
                /*
                ,(CASE WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>0 AND TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())<=24 THEN '24'
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>24 AND TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())<=48 THEN '48'
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>48 AND TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())<=72 THEN '72'
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>72 AND TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())<=96 THEN '96'
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>96 THEN '120'
                END) AS level_of_purchase1
                */
                ,(CASE 
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>48 AND TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())<=72 THEN 1
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>72 AND TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())<=96 THEN 2
                WHEN TIMESTAMPDIFF(HOUR,purchase.created_at,NOW())>96 THEN 3
                END) AS level_of_purchase
                
                FROM oms_laborder t0
                LEFT JOIN oms_laborder_purchase_order_line purchase
                ON t0.id=purchase.laborder_id
                LEFT JOIN oms_received_glasses received
                ON t0.id=received.lab_order_entity
                WHERE 1=1
                AND t0.status<>'CANCELLED'
                AND (t0.status='ASSEMBLING' or t0.status='GLASSES_RETURN')
                -- AND t0.vendor=5
                GROUP BY t0.lab_number
                ORDER BY hours_of_purchase DESC);
            '''
            with connections['default'].cursor() as cursor:
                cursor.execute(sql)
                logging.critical('Table created!')

        except Exception as e:
            logging.critical(str(e))

        logging.critical('generate lab orders completed ....')
