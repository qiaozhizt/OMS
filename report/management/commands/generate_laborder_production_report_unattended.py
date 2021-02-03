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

from report.models import LabOrderProductionReportController


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate laborder production report ....')

        index = 0

        try:
            lprc = LabOrderProductionReportController()
            lprc.generate_production_report()

        except Exception as e:
            logging.critical(str(e))

        logging.critical('generate laborder production report completed ....')
