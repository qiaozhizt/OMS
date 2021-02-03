# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.models.order_models import *
from oms.views import namedtuplefetchall
import logging
from django.db import connections
from django.db import transaction
from collections import namedtuple
import datetime,json

from wms.models import inventory_initial, inventory_struct, product_frame

class Command(BaseCommand):
    def handle(self, *args, **options):
        file = open("/lihf/ship_easupost.json", "r")
        content=file.read()
        file.close()
        j=json.loads(content)
        i=0
        for row in j:
            i=i+1
            if row["easypost_status"]=="delivered":
                print (row['lab_number'],row['ep_tracking_code'],row['lab_number'],row['easypost_datetime'])
                utc_date = datetime.datetime.strptime(row['easypost_datetime'], "%Y-%m-%dT%H:%M:%SZ")
                local_date = utc_date + datetime.timedelta(hours=8)
                local_date_str = datetime.datetime.strftime(local_date ,'%Y-%m-%d %H:%M:%S')
                LabOrder.objects.filter(lab_number=row['lab_number']).update(status='DELIVERED', delivered_at=local_date_str,tracking_code=row['ep_tracking_code'])
            else:
                LabOrder.objects.filter(lab_number=row['lab_number']).update(tracking_code=row['ep_tracking_code'])
                print(i)