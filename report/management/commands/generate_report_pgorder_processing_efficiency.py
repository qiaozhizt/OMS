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
from report.models import PgOrderProcessingReportController


class Command(BaseCommand):

    # def add_arguments(self, parser):
    #     # Positional arguments
    #     parser.add_argument('fileid', nargs='+', type=str)
    #     parser.add_argument(
    #         '--date',
    #         action='store_true',
    #         dest='date',
    #         default=False,
    #         help='start append start_date and end_date',
    #     )

    def handle(self, *args, **options):
        start_date = ''
        end_date = ''
        # options['fileid']
        # if options['date']:
        #     start_date = options['fileid'][0]
        #     end_date = options['fileid'][1]
        #     logging.debug(start_date)
        #     logging.debug(end_date)
        # else:
        #     logging.critical('请输入开始时间')

        pgc = PgOrderProcessingReportController()
        rm = pgc.generate_inlab_report(start_date, end_date)

        logging.debug("-------success-----")
