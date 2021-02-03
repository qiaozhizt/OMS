# -*- coding: utf-8 -*-
import logging
import time
from util.response import response_message
from django.core.management.base import BaseCommand

from wms.models import inventory_initial_lens, inventory_receipt_lens_controller


class Command(BaseCommand):
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('fileid', nargs='+', type=str)
        parser.add_argument(
            '--startid',
            action='store_true',
            dest='startid',
            default=False,
            help='start append id',
        )

    def handle(self, *args, **options):
        logging.critical('---开始从镜片库存初始化表-》写入-》镜片库存入库表---')
        rm = response_message()
        try:
            if options['startid']:
                for var in options['fileid']:
                    logging.critical('fileid=%s' % var)
                    fileid = var  # 获取输入的ID
            else:
                fileid = 1
            try:
                iils = inventory_initial_lens.objects.filter(id__gte=fileid).order_by("id")
            except Exception as e:
                logging.critical("错误：" + str(e))
                rm.capture_execption(e)
                rm.message = '获取初始化表出错'
            for iil in iils:
                # 写入
                # 通过时间获取编号
                time_now = time.strftime('%Y%m%d', time.localtime(time.time()))

                sku = iil.sku
                quantity = iil.quantity
                cyl = iil.cyl
                sph = iil.sph
                add = iil.add
                entity_id = iil.entity_id
                warehouse_code = iil.warehouse_code
                batch_number = ''  # iil.batch_number 在镜片库存表-批次 里自动生成
                irlc = inventory_receipt_lens_controller()
                # 当前默认上海仓
                rm = irlc.add('', time_now, 'INIT', warehouse_code, sku, float(quantity), float(sph), float(cyl), float(add),
                              0, '', '', batch_number, 'init')
            logging.critical('---写入-》镜片库存入库表完成---')
        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = '初始化表导入入库表出错'


class my_request:
    def __init__(self, my_user):
        self.user = my_user


class my_user:
    def __init__(self, id, name):
        self.id = id
        self.name = name
