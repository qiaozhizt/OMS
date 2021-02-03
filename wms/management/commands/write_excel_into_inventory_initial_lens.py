# -*- coding: utf-8 -*-
import logging
import xlrd
from util.response import response_message
from wms.models import inventory_initial_lens_controller
from django.core.management.base import BaseCommand


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
        logging.critical("******开始读取excel库存文件程序******")
        rm = response_message()
        try:
            if options['import']:
                for var in options['filename']:
                    logging.critical('filename=%s' % var)
                    filename = var
            else:
                rm.message = 'filename not found'
                return rm
            # 获取excel对象
            exl = xlrd.open_workbook(filename)
            # 获取第一张表
            sheet = exl.sheet_by_index(0)

            # 获取仓库代码
            warehouse_code = sheet.cell_value(1, 1)  # excel表中是2行B列
            logging.critical('warehouse_code=%s' % warehouse_code)
            # 获取sku
            sku = sheet.cell_value(2, 1)  # excel表中是3行B列
            logging.critical('sku=%s' % sku)
            # 获取最大行和列
            max_row = sheet.nrows
            max_col = sheet.ncols
            # 获取 sph cyl 列表
            cyl_list = sheet.row_values(6)  # 第6行
            sph_list = sheet.col_values(0)  # 第0列
            # 循环遍历数量,并写入初始化表
            for row in range(7, max_row - 3):
                sph = sph_list[row]  # 第3列的第row行
                for col in range(1, max_col):
                    cyl = cyl_list[col]  # 第2行的第col列
                    quantity = sheet.cell_value(row, col)
                    # 数量大于0才写入 初始化表
                    if quantity:
                        logging.critical("SPH=" + str(sph) + "，散光=" + str(cyl) + "，数量=" + str(quantity) + ', 开始写入')
                        iilc = inventory_initial_lens_controller()
                        rm = iilc.add(warehouse_code, sku, float(sph), cyl, 0, quantity, '', 'init')
                        logging.critical("写入结果=%s" % rm.message)
                    else:
                        logging.critical("SPH=" + str(sph) + "，散光=" + str(cyl) + "，数量=" + str(quantity) + ', 不写入')
            logging.critical("操作完成,%s" % rm.message)
        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = str(e)
