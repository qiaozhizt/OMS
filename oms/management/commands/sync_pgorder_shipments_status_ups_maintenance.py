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
import time
from django.db.models import Q

from django.http import HttpRequest
from oms.controllers.order_controller import *
from oms.models.order_models import PgOrderItem, LabOrder

from oms.controllers.pg_order_controller import pg_order_controller
import random


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start sync_pg_orderitem_ordertype ....')
        try:
            from util.ups import run
            from util.utils import LogHelper

            lh = LogHelper(settings.BASE_DIR + '/logs/sync_pgorder_shipments_status.csv')
            lh_error = LogHelper(settings.BASE_DIR + '/logs/sync_pgorder_shipments_status_error.csv')
            lbos = LabOrder.objects.filter(
                create_at__gte=time_delta_month_3()
                , ship_direction='EXPRESS'
                , status='DELIVERED').only(
                'id'
                , 'lab_number'
                , 'order_number'
                , 'shipping_number')

            lbos_count = lbos.count()

            shipping_numbers = {}

            idx = 1
            for lbo in lbos:
                sleep_life = random.randint(1, 9)

                try:
                    logging.critical('----------------------------------------')
                    logging.critical('sleep: %s Seconds ....' % sleep_life)
                    logging.critical('index: %s / count:%s' % (idx, lbos_count))

                    msg = ',%s,%s,%s' % (
                        lbo.order_number,
                        lbo.lab_number,
                        lbo.shipping_number)
                    logging.critical(msg)

                    shipping_number = lbo.shipping_number

                    if not shipping_numbers.has_key(shipping_number):
                        time.sleep(sleep_life)
                        shipping_numbers[shipping_number] = idx
                        data = run(shipping_number)
                        if data != '' and len(data) == 2:
                            if not data[0] == '':
                                dy = data[0]
                                dy = '%s:00' % dy
                                dy = dy.replace('/','-')
                                logging.critical('data0:%s' % dy)

                                td = datetime.datetime.strptime(dy, '%Y-%m-%d %H:%M:%S')
                                logging.critical('td:%s' % td)

                                LabOrder.objects.filter(
                                    order_number=lbo.order_number,
                                    shipping_number=lbo.shipping_number).update(
                                    delivered_at=td)

                                PgOrder.objects.filter(order_number=lbo.order_number).update(
                                    status='delivered'
                                    , delivered_at=td
                                )

                                tloc = tracking_lab_order_controller()

                                tk_lbos = LabOrder.objects.filter(
                                    order_number=lbo.order_number,
                                    shipping_number=lbo.shipping_number)

                                for tk_lbo in tk_lbos:
                                    tloc.tracking(tk_lbo, None, 'DELIVERED', '妥投')

                                lh.write(msg)
                        else:
                            lh_error.write(msg)
                except Exception as ex:
                    logging.error(str(ex))
                else:
                    logging.critical('Shipping Number Duplicated ....')

                idx += 1

        except Exception as e:
            logging.critical(str(e))

        logging.critical('end sync_pg_orderitem_ordertype ....')
