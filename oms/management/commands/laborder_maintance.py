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
from oms.models.order_models import LabOrder, PgOrderItem


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info("Preparing PgOrder & Items maitance ....")

        lbos = LabOrder.objects.filter(order_number='')

        for lbo in lbos:
            pgi = PgOrderItem.objects.get(id=lbo.base_entity)
            lbo.order_number = pgi.order_number
            lbo.save()
            logging.info('lab number: %s' % lbo.order_number)

        logging.info('Completed.')
