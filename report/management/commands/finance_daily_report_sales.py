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

from report.finance_reports import *


class Command(BaseCommand):
    """
    Daily Report Finance
    created by guof.
    2020.02.26
    """

    def handle(self, *args, **options):
        logging.critical('start Finance Daily Report Sales ....')

        try:

            fr = FinanceReport()
            fr.handle_daily_report_sales()

        except Exception as e:
            logging.critical(str(e))

        logging.critical('Finance Daily Report Sales completed ....')
