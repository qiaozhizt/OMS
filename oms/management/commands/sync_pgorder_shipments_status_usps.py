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
import random


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start sync_pg_orderitem_ordertype ....')
        try:
            from util.usps import read_ups_by_track_numbers
            from util.utils import LogHelper
            from util.format_helper import get_datetime_by_en_str
            start_date = '2020-01-01 00:00:00'
            sd = datetime.datetime.strptime(start_date, '%Y-%m-%d %H:%M:%S')
            lh = LogHelper(settings.BASE_DIR + '/logs/sync_pgorder_shipments_status.csv')
            lh_error = LogHelper(settings.BASE_DIR + '/logs/sync_pgorder_shipments_status_error.csv')
            lbos = LabOrder.objects.filter(
                # create_at__gte=time_delta_month_3(),
                create_at__gte=sd,
                status='SHIPPING').filter(
                act_ship_direction='STANDARD') \
                .only(
                'id',
                'lab_number',
                'order_number',
                'tracking_code')

            lbos_count = lbos.count()

            tracking_codes = {}

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
                        lbo.tracking_code)
                    logging.critical(msg)

                    tracking_code = lbo.tracking_code

                    if not tracking_codes.has_key(tracking_code):
                        time.sleep(sleep_life)
                        tracking_codes[tracking_code] = idx
                        data = read_ups_by_track_numbers(tracking_code)
                        if data != '' and len(data) == 3:
                            if not data[0] == '':

                                str1 = '%s %s' % (data[0],data[1])
                                td  = get_datetime_by_en_str(str1)

                                #td = datetime.datetime.strptime(dy, '%Y-%m-%d %H:%M:%S')
                                logging.critical('td:%s' % td)

                                LabOrder.objects.filter(
                                    order_number=lbo.order_number,
                                    tracking_code=lbo.tracking_code).update(
                                    status='DELIVERED'
                                    , delivered_at=td)

                                poc = pg_order_controller()
                                poc.set_order2delivered(None,lbo.order_number,td)

                                tloc = tracking_lab_order_controller()

                                tk_lbos = LabOrder.objects.filter(
                                    order_number=lbo.order_number,
                                    tracking_code=lbo.tracking_code)

                                for tk_lbo in tk_lbos:
                                    tloc.tracking(tk_lbo, None, 'DELIVERED', '妥投')

                                lh.write(msg)
                        else:
                            lh_error.write(msg)
                except Exception as ex:
                    logging.error(str(ex))
                else:
                    logging.critical('Tracking Code Duplicated ....')

                idx += 1

        except Exception as e:
            logging.critical(str(e))

        logging.critical('end sync_pg_orderitem_ordertype ....')
