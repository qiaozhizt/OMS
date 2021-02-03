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
from django.db import connections
from django.db import transaction

from wms.models import inventory_struct, inventory_struct_warehouse


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start maintance inventory structs ....')

        index = 0

        try:
            logging.critical('start ....')

            oiss = inventory_struct.objects.all()

            for ois in oiss:
                oisw = inventory_struct_warehouse()
                oisw.sku = ois.sku
                oisw.name = ois.name
                oisw.quantity = ois.quantity
                oisw.user_id = 1
                oisw.user_name = 'SYSTEM'
                oisw.warehouse_code = 'W01'
                oisw.warehouse_name = '本部'

                oisw.save()

                logging.critical('insert - %s' % ois.sku)


        except Exception as e:
            logging.critical(e.message)

        logging.critical('completed ....')
