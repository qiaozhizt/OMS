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
from oms.models.order_models import PgOrderItem, LabOrder

from oms.controllers.pg_order_controller import pg_order_controller
from oms.controllers.lab_order_controller import lab_order_controller
import random


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start sync_pg_orderitem_ordertype ....')
        try:
            from util.ups import run
            from util.utils import LogHelper

            start_date = '2020-01-01 00:00:00'
            sd = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')

            lh = LogHelper(settings.BASE_DIR + '/logs/sync_pgorder_shipments_tracking_code_maintenance.csv')
            lbos = LabOrder.objects.filter(
                create_at__gte=sd
                , status='SHIPPING').filter(
                act_ship_direction='STANDARD'
            ) \
                .only(
                'id',
                'lab_number',
                'order_number',
                'shipping_number')

            lbos_count = lbos.count()

            idx = 1
            for lbo in lbos:

                try:
                    logging.critical('----------------------------------------')
                    logging.critical('index: %s / count:%s' % (idx, lbos_count))

                    msg = ',%s,%s,%s' % (
                        lbo.order_number,
                        lbo.lab_number,
                        lbo.shipping_number)
                    logging.critical(msg)

                    shipping_number = lbo.shipping_number
                    lab_number = lbo.lab_number

                    sleep_life = random.randint(1, 2)
                    logging.critical('sleep: %s Seconds ....' % sleep_life)
                    time.sleep(sleep_life)
                    loc = lab_order_controller()
                    resp = loc.get_tracking_code(lab_number=lab_number)
                    logging.debug(resp)

                    tracking_code = resp.get('data', '')
                    if tracking_code:
                        LabOrder.objects.filter(lab_number=lab_number).update(tracking_code=tracking_code)
                        lh.write(msg)
                    else:
                        logging.debug('tracking is null, passed ....')
                except Exception as ex:
                    logging.error(str(ex))

                idx += 1

        except Exception as e:
            logging.critical(str(e))

        logging.critical('end sync_pg_orderitem_ordertype ....')

    def _get_tracking_code(self, lab_number):
        pass
