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

from oms.controllers.lab_order_controller import lab_order_controller
from pg_oms.settings import *
from oms.models.order_models import LabOrder
from mrp.contollers import job_contoller


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start job tracking ....')
        AI_CODE = 'AI_90410'

        try:
            jc = job_contoller()
            start_day = jc.start_day

            logging.critical('start day:%s' % start_day)

            lbos = LabOrder.objects.filter(~Q(status='SHIPPING'), ~Q(status='COMPLETE'), ~Q(status='CANCELLED')).filter(
                create_at__gte=start_day)

            for lbo in lbos:
                parameters = {}
                parameters['lbo'] = lbo
                jc.tracking(parameters)
                logging.critical('Lab Number:%s Status:%s' % (lbo.lab_number, lbo.status))

        except Exception as ex:
            logging.critical(str(ex))

        logging.critical('job tracking ending ....')
