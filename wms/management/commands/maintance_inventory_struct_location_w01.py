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

        logging.critical('start ....')
        with open('skus_location.csv') as inv_file:
            line = inv_file.readline()
            while line:
                lines = line.split(',')
                sku = lines[0]
                location = lines[1]

                logging.critical(sku)
                logging.critical(location)

                try:
                    isw = inventory_struct_warehouse.objects.get(warehouse_code='W01',sku=sku)
                    logging.critical(isw.quantity)
                    isw.location = location
                    isw.save()

                except Exception as ex:
                    logging.error(str(ex))

                line = inv_file.readline()

        logging.critical('所有操作成功结束 ....')

        logging.critical('completed ....')
