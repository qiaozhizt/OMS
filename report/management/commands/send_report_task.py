# -*- coding: utf-8 -*-
import logging
import time
import datetime

from django.core.management.base import BaseCommand
from report.production_daily_report_task import statistical_report, send_report
import logging

_logger = logging.getLogger('mrp')
class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('name', nargs='*', type=str)

    def handle(self, *args, **options):
        send_report()
