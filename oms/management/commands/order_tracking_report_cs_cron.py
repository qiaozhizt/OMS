# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.management.base import BaseCommand

from oms.models.order_tracking_report_cs_models import OrderTrackingReportCS
from oms.models.order_models import *

import logging



class Command(BaseCommand):
    def handle(self,*args, **options):
        queryset_cs = OrderTrackingReportCS.objects.all()
        logging.debug("开始执行数据维护。。。。")
        if queryset_cs:
            for cs in queryset_cs:
                if cs.pgorder_number == None or cs.pgorder_number == '':
                    logging.debug("维护数据%s"%cs.order_number)
                    lo = LabOrder.objects.get(lab_number = cs.order_number)
                    poi = PgOrderItem.objects.get(pk=lo.base_entity)
                    cs.pgorder_number = poi.order_number
                    cs.shipping_method = poi.shipping_method
                    cs.save()

            logging.debug("-----------success---------")
        else:
            logging.debug("无数据可维护")

