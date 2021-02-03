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
from oms.models.order_models import LabOrder


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate lab orders ....')

        index = 0

        try:
            lbos = LabOrder.objects.all()
            for lbo in lbos:
                lbo.act_ship_direction = lbo.ship_direction
                lbo.save()
                logging.critical('lab number: %s processed ....' % lbo.lab_number)


        except Exception as e:
            logging.critical(e.message)

        logging.critical('generate lab orders completed ....')
