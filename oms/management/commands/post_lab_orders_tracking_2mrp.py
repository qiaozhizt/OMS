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
from oms.models.post_models import Prescription
from oms.models.product_models import PgProduct
from oms.models.ordertracking_models import *

from oms.controllers.lab_order_controller import lab_order_controller
from pg_oms.settings import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start post lab orders trackings ....')
        try:
            ots = OrderTracking.objects.filter(is_sync=False)

            count = ots.count()
            index = 0

            for ot in ots:
                index += 1
                try:
                    logging.critical('Index: %s / %s' % (index, count))
                    if ot.is_sync:
                        logging.critical('Order is Sync, pass ....')
                        continue
                    tloc = tracking_lab_order_controller()
                    tloc.post2mrp(ot)
                    logging.critical('Post Ok!')
                except Exception as ex:
                    logging.critical(str(ex))

        except Exception as e:
            logging.critical(str(e))

        logging.critical('post lab orders trackings completed ....')
