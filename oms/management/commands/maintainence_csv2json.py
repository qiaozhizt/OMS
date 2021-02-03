# -*- coding: utf-8 -*-
import logging
from util.response import response_message
from wms.models import inventory_initial_lens_controller
from django.core.management.base import BaseCommand
import time


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
            if options['import']:
                for var in options['filename']:
                    logging.critical('filename=%s' % var)
                    filename = var
            else:
                rm.message = 'filename not found'
                return rm
            logging.critical('filename: %s' % filename)
            with open(filename) as fobj:
                line = fobj.readline()
                while line:
                    line = line.strip()
                    logging.critical('%s-%s' % (lbo_count, line))
                    lbo_count += 1
                    line = fobj.readline()

            logging.critical('%s orders need remake ....' % lbo_count)

            logging.critical('after 10 seconds will start remake ....')
            time.sleep(10)

        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
