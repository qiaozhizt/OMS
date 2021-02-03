# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.management.base import BaseCommand
from oms.models.order_models import LabOrder
import logging


class Command(BaseCommand):
    def handle(self,*args, **options):
        los = LabOrder.objects.all()
        logging.debug("###############开始维护act_lens数据###################")
        for lo in los:
            logging.debug("正在处理订单%s"%lo)
            if lo.act_lens_sku == None or lo.act_lens_name == '':
                lo.act_lens_sku = lo.lens_sku
                lo.act_lens_name = lo.lens_name
                lo.save()

        logging.debug("------------------complete-----------------")
        logging.debug("------------------success------------------")