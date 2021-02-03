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

from report.models import lens_report_control


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start generate lens report ....')

        index = 0

        try:
            lrc = lens_report_control()
            lrc.generate()

        except Exception as e:
            logging.critical(e.message)

        logging.critical('generate lens report completed ....')
