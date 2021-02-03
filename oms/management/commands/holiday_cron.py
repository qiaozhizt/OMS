# -*- coding: utf-8 -*-
from __future__ import unicode_literals


from django.core.management.base import BaseCommand
from oms.models.holiday_setting_models import HolidaySetting
import logging
import datetime
from django.util import timezone

"""holidaysetting数据维护"""
class Command(BaseCommand):
    def handle(self,*args, **options):
        now_year = timezone.now().year     #获取年份
        now_date = timezone.now().weekday() #获取当前时间是周几0-6
        logging.debug("---准备。。。。。")
        logging.debug("--------开始维护%s年周日日期"%now_year)
        if now_date <> 6:
            sunday = timezone.now()+datetime.timedelta(6-now_date)
        else:
            sunday = timezone.now()
        hs = HolidaySetting()
        try:
            date = hs.query_by_holiday(sunday) #判断当前时间是否已经存在数据库
            logging.debug('------数据已存在。。。。')
        except Exception as e:
            logging.debug("当前日期不在数据库中,添加到数据库。。。")
            logging.debug("当前日期==>%s" % sunday)
            hs.add_holiday(sunday)


        while sunday.year == now_year :     #自第一个周日日期循环取一整年的周日日期
            sunday = sunday + datetime.timedelta(7)
            if sunday.year == now_year:
                hsd = HolidaySetting()
                # if holiday_list:
                try:
                    date = hs.query_by_holiday(sunday)
                    logging.debug('------数据已存在。。。。')
                    continue
                except Exception as e:
                    logging.debug("当前日期不在数据库中,添加到数据库。。。")
                    logging.debug("当前日期==>%s"%sunday)
                    hsd.add_holiday(sunday)
            else:
                break



        logging.debug("-------------success---------------")



