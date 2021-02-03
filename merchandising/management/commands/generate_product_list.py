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
from merchandising.models import ProductParent,Product,ProductListController

class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate product list ....')

        index = 0

        try:
            plc = ProductListController()
            plc.GenerateAll()

        except Exception as e:
            logging.critical(e.message)

        logging.critical('generate product list completed ....')
