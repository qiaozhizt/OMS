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
from oms.models.order_models import *


class Command(BaseCommand):
    def handle(self, *args, **options):

        poc = PgOrderController()

        logging.debug("Preparing generate PgOrder Addtional ....")

        poc.generate_order_addtional()


