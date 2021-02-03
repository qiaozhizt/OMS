# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.db import connections
import xlrd

from wms.models import inventory_initial, inventory_struct, product_frame

class Command(BaseCommand):
    def handle(self, *args, **options):
        # 打开文件
        data = xlrd.open_workbook('/lihf/需同步追踪号和更改妥投状态11.1.xlsx')

        # 查看工作表
        # data.sheet_names()
        table = data.sheet_by_name('更改为妥投状态')
        # 打印data.sheet_names()可发现，返回的值为一个列表，通过对列表索引操作获得工作表1
        # table = data.sheet_by_index(0)

        # 获取行数和列数
        # 行数：table.nrows
        # 列数：table.ncols
        print("总行数：" + str(table.nrows))
        print("总列数：" + str(table.ncols))
        for row in range(1,table.nrows):
#             tracking_code= table.cell(row,0).value
#             increment_id= str(table.cell(row,1).value)[:-2]
#             box_id= str(table.cell(row,2).value)[:-2]
#             sql="""SELECT box_item.*
# FROM `shipment_glasses_box` box
# INNER JOIN `shipment_glasses_box_item` box_item ON box_item.`box_id`=box.`box_id`
# WHERE
# box.`box_id`={0}
# AND box_item.`order_number`='{1}' AND tracking_code='{2}'""".format(box_id,increment_id,tracking_code)
#             with connections["pg_oms_query"].cursor() as cursor:
#                 print(sql)
#                 cursor.execute(sql)
#                 pgos = namedtuplefetchall(cursor)
#                 print(pgos)
            laborder_number=table.cell(row,2).value
            if laborder_number.__len__()>0:
                with connections['default'].cursor() as cursor:
                    update_sql = """UPDATE oms_laborder SET `status`='DELIVERED' WHERE lab_number='{0}'""".format(laborder_number)
                    print(update_sql)
                    cursor.execute(update_sql)