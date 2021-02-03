# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.views import namedtuplefetchall
import logging
from django.db import connections
import codecs
from wms.models import *


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.info('transfer_lens_from_danyang_to_sh_maintenance start ....')
        try:
            # 查询所有丹阳仓库镜片结构-待出库清单-txt
            sql_out = '''
            /*
             出库使用的脚本
            */
            SELECT
                sku,
                NAME,
                base_sku,
                sph,
                cyl,
                warehouse_code,
                warehouse_name,
                batch_number,
                quantity
            FROM
                wms_inventory_struct_lens_batch
            WHERE
                warehouse_code = 'L01'
            AND sku IN (
                '0b57944a-ae05-4670-8845-d0a0c66ccb59',
                '1f341a86-f5ce-44fc-88cc-7068eac65ff6',
                '4b7e09f3-f706-4a88-b734-2c098008be09',
                '89f4494e-4d83-434a-a039-6b71b832a40e',
                'a94fabf8-eaa0-4b87-a57e-bdbea8ba18ee',
                'bd05f8ca-b91a-4a8c-889b-caf74ade4cc1'
            )
            AND quantity > 0
            '''

            file_log = './data/danyang_stock_log.txt'
            lw = codecs.open(file_log, 'a', 'utf-8')
            file_out = './data/danyang_stock_out_qty.txt'
            writer = codecs.open(file_out, 'a', 'utf-8')

            with connections['default'].cursor() as cursor:
                cursor.execute(sql_out)
                results = namedtuplefetchall(cursor)
                for r in results:
                    line = '%s,%s,%s,%s,%s,%s,%s,%s,%s\n' % (
                        r.sku, r.NAME, r.base_sku, r.sph, r.cyl, r.warehouse_code, r.warehouse_name, r.batch_number,
                        r.quantity)
                    logging.critical(line)
                    writer.write(line)

            writer.close()

            # 查询所有丹阳仓库镜片结构-待入库清单-txt
            sql_in = '''
            /*
             入库使用的脚本
            */
            SELECT
                sku,
                sph,
                cyl,
                warehouse_code,
                sum(quantity) AS quantity
            FROM
                wms_inventory_struct_lens_batch
            WHERE
                warehouse_code = 'L01'
            AND sku IN (
                '0b57944a-ae05-4670-8845-d0a0c66ccb59',
                '1f341a86-f5ce-44fc-88cc-7068eac65ff6',
                '4b7e09f3-f706-4a88-b734-2c098008be09',
                '89f4494e-4d83-434a-a039-6b71b832a40e',
                'a94fabf8-eaa0-4b87-a57e-bdbea8ba18ee',
                'bd05f8ca-b91a-4a8c-889b-caf74ade4cc1'
            )
            AND quantity > 0
            GROUP BY
                sku,
                sph,
                cyl,
                warehouse_code
            '''

            file_in = './data/danyang_stock_in_qty.txt'
            writer = codecs.open(file_in, 'a', 'utf-8')

            with connections['default'].cursor() as cursor:
                cursor.execute(sql_in)
                results = namedtuplefetchall(cursor)
                for r in results:
                    line = '%s,%s,%s,%s,%s\n' % (
                        r.sku, r.sph, r.cyl, r.warehouse_code, r.quantity)
                    logging.critical(line)
                    writer.write(line)
            writer.close()

            # 依据出库清单对应批次 从L01出库
            idlc = inventory_delivery_lens_controller()

            with codecs.open(file_out, 'r', 'utf-8') as reader:
                lines = reader.readlines()
                for line in lines:
                    line = line.replace('\n', '')
                    if not line:
                        continue
                    rows = line.split(',')

                    sku = rows[0]
                    sph = rows[3]
                    cyl = rows[4]
                    # warehouse_code = rows[5]
                    batch_number = rows[7]
                    quantity = rows[8]

                    rm = idlc.add(None, '20191123', 'ALLOTTED_OUT', 'L01', sku, sph, cyl, 0.00, quantity,
                                  batch_number, '系统自动调整-20191123')
                    if rm.code != 0:
                        msg = 'ERROR(%s),%s\n' % (rm.message, line)
                        lw.write(msg)

            # 依据入库清单 按201900批次入库到L02
            irlc = inventory_receipt_lens_controller()

            with codecs.open(file_in, 'r', 'utf-8') as reader:
                lines = reader.readlines()
                for line in lines:
                    line = line.replace('\n', '')
                    if not line:
                        continue
                    rows = line.split(',')

                    sku = rows[0]
                    sph = rows[1]
                    cyl = rows[2]
                    quantity = rows[4]

                    rm = irlc.add(None, '20191123', 'ALLOTTED_IN', 'L02', sku, quantity, sph, cyl, 0.00, 0, '', '', '',
                                  '系统自动调整-20191123', '')

                    if rm.code != 0:
                        msg = 'ERROR(%s),%s\n' % (rm.message, line)
                        lw.write(msg)

            lw.close()

            # 关闭镜片批次管理

            logging.info('end ....')
        except Exception as e:
            logging.exception(e.message)

        logging.critical('transfer_lens_from_danyang_to_sh_maintenance end ....')
