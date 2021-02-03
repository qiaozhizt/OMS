# -*- coding: utf-8 -*-

import logging
import requests
import datetime

from util.db_helper import *
from util.response import *
from util.dict_helper import *
from util.format_helper import *
from oms.models.order_models import LabOrder,LabProduct
from oms.models.utilities_models import *
from wms.models import inventory_struct_lens, product_frame
from vendor.models import lens
from pg_oms import settings


class stockorder_to_laborder_controller:

    def create_laborder(self, data_dict, flag):
        data = {}
        try:
            order_number = data_dict['stock_order_number']
            order_number_part = order_number[9:]
            order_date = datetime.datetime.now()
            year = order_date.year
            str_year = str(year)
            year_part = str_year[len(str_year) - 1:len(str_year)]
            month = order_date.month
            str_month = str(month)
            if len(str_month) == 1:
                str_month = '0' + str_month
            day = order_date.day
            str_day = str(day)
            if len(str_day) == 1:
                str_day = '0' + str_day
            if flag == 'list':
                qty = data_dict['remaining_qty']
            else:
                qty = data_dict['lab_qty']

            last_laborders = LabOrder.objects.filter(lab_number__contains=order_number_part).order_by("-id")
            if len(last_laborders) > 0:
                str_count = last_laborders[0].lab_number.split("-")[-1]
                if "T" in str_count:
                    count = 1
                else:
                    count = int(str_count) + 1
            else:
                count = 0

            inv_struct_lens = inventory_struct_lens.objects.filter(sku=data_dict['od_lens_sku'])
            sku = inv_struct_lens[0].base_sku
            if '-' in sku[0:2]:
                vendor =sku[:1]
            else:
                vendor =sku[:2]

            lens_list = lens.objects.filter(sku=sku)
            if len(lens_list) > 0:
                lens_name = lens_list[0].name
            else:
                lens_name = inv_struct_lens[0].name.replace("-近视", "").replace("-老花", "")

            pf_lists = product_frame.objects.filter(sku=data_dict['frame'])
            if len(pf_lists) == 0:
                image = ''
                thumbnail = ''
            else:
                pf = pf_lists[0]
                image = pf.image
                thumbnail = pf.thumbnail

            for i in range(1, int(qty)+1):
                lab_order_number = year_part + str_month + str_day + '-' + order_number_part + '-' + str(i) + "T" + str(
                    qty)
                if count > 0:
                    lab_order_number = lab_order_number + "-" + str(count)
                lbo = LabOrder()
                # General
                lbo.lab_number = lab_order_number
                lbo.order_number = order_number
                lbo.base_entity = data_dict['id']
                lbo.type = 'STKO'
                lbo.chanel = ''
                lbo.is_vip = False
                lbo.tag = 'WEBSITE'
                lbo.ship_direction = 'EMPLOYEE'
                lbo.act_ship_direction = 'EMPLOYEE'

                lbo.order_date = order_date
                lbo.order_datetime = datetime.datetime.strptime(data_dict['start_date'], '%Y-%m-%d %H:%M:%S')
                lbo.frame = data_dict['frame']
                lbo.lens_sku = ''
                lbo.quantity = 1
                lbo.vendor = vendor

                if int(vendor)<10:
                    lbo.lens_sku = inv_struct_lens[0].base_sku[2:]
                else:
                    lbo.lens_sku = inv_struct_lens[0].base_sku[3:]

                lbo.lens_name = lens_name
                lbo.act_lens_name = lens_name
                lbo.act_lens_sku = inv_struct_lens[0].base_sku
                lbo.od_sph = data_dict['od_lens_sph']
                lbo.od_cyl = data_dict['od_lens_cyl']
                lbo.os_sph = data_dict['os_lens_sph']
                lbo.os_cyl = data_dict['os_lens_cyl']
                lbo.comments = data_dict['comments']
                lbo.comments_inner = ''

                lbo.estimated_ship_date = order_date+ datetime.timedelta(days=7)
                lbo.estimated_time = order_date+ datetime.timedelta(days=7)
                lbo.estimated_date = order_date+ datetime.timedelta(days=7)
                lbo.targeted_date = order_date+ datetime.timedelta(days=7)
                lbo.image = image
                lbo.thumbnail = thumbnail
                lbo.save()
                bar_img_src = utilities.createC128(str("%s%s" % (settings.BAR_CODE_PREFIX, lbo.id)), lbo.create_at)
                lbo.c128_path = bar_img_src
                lbo.save()

            data['code'] = 0
            data['message'] = "Success"
            return data
        except Exception as e:
            data['code'] = -1
            data['message'] = e
            return data
