# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.management.base import BaseCommand
from oms.models.holiday_setting_models import HolidaySetting
import logging

from report.models import LabOrderProductionReportController

"""laborder production report 生产报表"""
class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('fileid', nargs='+', type=str)
        parser.add_argument(
            '--date',
            action='store_true',
            dest='date',
            default=False,
            help='start append laborder date',
        )
    def handle(self,*args, **options):
        start_date = ''
        end_date = ''
        if options['date']:
            start_date = options['fileid'][0]
            end_date = options['fileid'][1]
        else:
            logging.critical('请输入laborder date')

        pgc = LabOrderProductionReportController()
        rm = pgc.generate_production_report(start_date, end_date)

        logging.debug("-------------success---------------")



