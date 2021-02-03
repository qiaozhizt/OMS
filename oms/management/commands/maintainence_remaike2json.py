# -*- coding: utf-8 -*-
import logging
from util.response import response_message
from wms.models import inventory_initial_lens_controller
from django.core.management.base import BaseCommand
import time
import simplejson as json

from pg_oms import settings
from django.db import connections
from django.db import transaction
from util.base_type import base_type
from util.response import response_message
from util.db_helper import *
from util.dict_helper import *
from util.format_helper import *
from util.utils import *

class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('filename', nargs='+', type=str)
        parser.add_argument(
            '--import',
            action='store_true',
            dest='import',
            default=False,
            help='noe founed filename',
        )

    def handle(self, *args, **options):
        # 每次读一个EXCEL文件的第一张表
        logging.critical("******开始读取文件******")
        rm = response_message()
        try:
            file_name = ""
            if options['import']:
                for var in options['filename']:
                    logging.critical('filename=%s' % var)
                    filename = var
            else:
                rm.message = 'filename not found'
                return rm
            logging.critical('filename: %s' % filename)
            full_name = '%s/%s' % (settings.BASE_DIR,filename)
            logging.debug(full_name)
            sql = """
                select order_number as origin_order_number,item_id as origin_item_id,create_at as created_at,frame from oms_pgorderitem where id in (select base_entity from oms_laborder where date(create_at)>=date('2020.01.01') 
                and lab_number like '%-R%');
            """
            json_data = []
            obj = {}
            with connections['default'].cursor() as cursor:
                cursor.execute(sql)
                items = dictfetchall(cursor)
            
            json_data = json.dumps(items, cls=DateEncoder)

            logging.debug(json_data)
            fh = FileHelper(full_name)
            fh.write(json_data)
            
            logging.critical('after 10 seconds will start remake ....')

        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
