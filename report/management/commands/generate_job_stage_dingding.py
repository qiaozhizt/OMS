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

from report.job_stage_reports import JobStageReport


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate job stage report ....')

        index = 0

        try:
            jsr = JobStageReport()
            jsr.handle_daily_report()
            # jsr.get_lab_order_status_report()


        except Exception as e:
            logging.critical(e.message)

        logging.critical('generate job stage report completed ....')
