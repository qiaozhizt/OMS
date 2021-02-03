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


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate lab orders ....')

        index = 0

        # Pg Order List:
        pgos = PgOrder.objects.filter(is_enabled=True,
                                      status_control='APPROVED',
                                      is_inlab=False,
                                      status='processing')
        # pgos = pgos.filter(~Q(status='holded')
        #                    | ~Q(status='canceled')
        #                    | ~Q(status='closed')
        #                    | ~Q(status='complete')
        #                    | ~Q(status='shipped')
        #                    | ~Q(status='fraud')
        #                    )
        logging.critical(pgos.query)

        msg = '(%s):%s: %s'

        for pgo in pgos:
            logging.critical(msg % (str(index),pgo.order_number,pgo.status))
            index += 1
            poc = PgOrderController()
            res = poc.generate_lab_orders(pgo.order_number)
            logging.critical(res)

        for pgo in pgos:
            ods = []
            ods.append(pgo.order_number)
            poc = PgOrderController()
            res = poc.pgorder_address_verified(ods)
            logging.critical(res)

        logging.critical('generate lab orders completed ....')
