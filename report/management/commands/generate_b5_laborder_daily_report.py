# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time
import datetime
from django.db import connections
from django.db import transaction

from django.core.management.base import BaseCommand
from util.db_helper import *
import codecs
from api.models import DingdingChat
from pg_oms import settings

class Command(BaseCommand):

    def handle(self, *args, **options):
        logging.critical('generate_b5_laborder_daily_report')
        sql = """
        SELECT DAY(create_at) AS SalesDay,SUM(quantity) AS FrameCount FROM oms_pgorderitem
            WHERE date_format(create_at, '%Y %m %d') = date_format(DATE_SUB(curdate(), INTERVAL 0 MONTH),'%Y %m %d')
            AND STATUS<>'CANCELLED'
        """
        file = settings.RUN_DIR + '/generate_b5_laborder_daily_report.txt'
        quantity = 0
        with codecs.open(file, 'r', 'utf-8') as reader:
            lines = reader.readlines()
            if len(lines) > 0:
                line = lines[len(lines) - 1]
                columns = line.split(',')
                if columns[1]:
                    quantity = int(columns[1])

        with connections['pg_oms_query'].cursor() as cursor:
            cursor.execute(sql)
            results = namedtuplefetchall(cursor)
            for r in results:
                with codecs.open(file, 'a', 'utf-8') as writer:
                    dtnow = datetime.datetime.now()
                    if r.FrameCount:
                        line = '\n%s,%s' % (dtnow, r.FrameCount)
                        writer.write(line)
                    report = ''
                    msg = 'Now: %s\n' % (dtnow)
                    report += msg

                    msg = '--------------------\n'
                    report += msg

                    msg = 'Total Today: %s\n' % r.FrameCount
                    report += msg

                    diff = 0
                    if r.FrameCount:
                        diff = int(r.FrameCount) - quantity
                    msg = 'Last Hour: %s\n' % diff
                    report += msg

                    logging.critical(report)

                    # send dingding message to test chat
                    # 黑五实时报表群
                    ddc = DingdingChat()
                    ddc.send_text_to_chat('chat98bdad66e89d71447bee24f3d2664e4e', report)
