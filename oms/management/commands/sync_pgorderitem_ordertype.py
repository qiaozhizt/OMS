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



class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start sync_pg_orderitem_ordertype ....')
        try:
            pgis = PgOrderItem.objects.filter(order_type='')
            pgis_count = pgis.count()

            logging.critical("There is [%s] record in todo list ." % pgis_count)

            calculate_times = int(pgis_count / 100) + 1
            poc = pg_order_controller()
            for idx in range(1, calculate_times):
                logging.critical("Current Index [%s]/[%s] ...." % (idx, calculate_times))
                try:
                    start_index = (idx-1) * 100
                    end_index = idx * 100
                    for item in pgis[start_index:end_index]:
                        data_dict = {
                            "lens_sku": item.lens_sku,
                            "tint_name": item.tint_name
                        }
                        logging.critical("data_dict [%s] ...." % (data_dict))
                        order_type = poc.get_order_type(data_dict)
                        logging.critical("order_type [%s] ...." % (order_type))
                        item.order_type = order_type
                        item.save()
                        LabOrder.objects.filter(order_number=item.order_number).update(order_type=order_type)
                    time.sleep(5)
                except Exception as ex:
                    logging.critical('sync_pg_orderitem_ordertype: %s' % str(ex))
        except Exception as e:
            logging.critical(str(e))

        logging.critical('end sync_pg_orderitem_ordertype ....')
