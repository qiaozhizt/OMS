# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.models.order_models import LabOrder
import logging
import datetime
from django.utils import timezone
from django.db import connections
from util.db_helper import namedtuplefetchall
from util.db_helper import DbHelper

class Command(BaseCommand):
    def handle(self, *args, **options):
        now = timezone.now()
        timedel = now + datetime.timedelta(days=-60)
        sql ="""SELECT lab_number FROM oms_laborder WHERE `status` NOT IN ('SHIPPING', 'COMPLETE', 'CANCELLED', 'DELIVERED') AND create_at >='%s'""" % timedel
        logging.debug("---------开始执行command---------")
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute(sql)
                for item in namedtuplefetchall(cursor):
                    lo = LabOrder.objects.get(lab_number=item.lab_number)
                    set_time = lo.set_time_calculate()
                    production_days = lo.production_days_calculate()
                    update_sql = """
                    UPDATE oms_laborder SET set_time='%s', production_days='%s' 
                    WHERE lab_number='%s'""" % (set_time, production_days, item.lab_number)
                    DbHelper.execute(update_sql)
            logging.debug("--------successful complate--------")
        except Exception as e:
            logging.debug("Error==>%s" % e)
        finally:
            cursor.close()

# class Command(BaseCommand):
#     help = "test command"
#
#     def handle(self,*args, **options):
#         self.stdout.write("sdfosdlf")
