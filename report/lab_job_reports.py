# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
import logging
import datetime
import time
from datetime import timedelta
from django.db import connections, transaction
from report.models import ReportConfig, ReportInfo, ReportInfoLine
from util.db_helper import namedtuplefetchall, dictfetchall

from django.http import HttpRequest
import pandas as pd
from StyleFrame import StyleFrame, Styler, utils
from dingtalk import SecretClient, AppKeyClient
from dingtalk.model import message
from urllib3 import encode_multipart_formdata
import requests
import simplejson as json

from util.db_helper import *
from util.dict_helper import *
from pg_oms import settings

from oms.models.order_models import LabOrder


class LabJobReport:
    """
    Finance Report
    created by guof.
    2019.12.30

    updated by guof.
    2019.12.31

    updated by guof.
    2020.01.05 00:00
    """

    def handle_daily_report(self):
        '''
        Daily Report
        :return:
        '''
        logging.critical('start Daily Report Finance ....')
        index = 0
        try:

            logging.debug("start ....")

            file_name = self.get_daily_report_data()
            logging.debug('file name: %s' % file_name)

            now = datetime.datetime.now()
            now_s = now.strftime("%Y-%m-%d")
            txt_body = "LAB JOB HC订单汇总[%s]\n" % now_s

            if file_name == 'NULL':
                logging.critical('No data')
            else:
                logging.critical(file_name)
                self.ding_msg(file_name, txt_body)

            logging.debug("completed ....")

        except Exception as e:
            logging.critical(str(e))

        logging.critical('Daily Report Finance completed ....')

    # Generate Daily Report
    def get_daily_report_data(self):

        file_name = "%s/report/data/lab_job_daily_report/lab_job_daily_report_%s.xlsx"

        now = datetime.datetime.now()
        now_s = now.strftime("%Y-%m-%d %H-%m-%s")
        file_name = file_name % (settings.RUN_DIR, now_s)


        sqls = self.get_yesterday_sql()

        sql = sqls['lab_job_hc']
        data = self.get_data(sql)

        if len(data['items'])>0:
            ew = StyleFrame.ExcelWriter(file_name)
            self.write2xl(ew, data['titles'], data['items'], "HC订单明细%s" % sqls['title_parameters'])

            for item in data['items']:
                logging.critical(item.lab_number)
                lbo = LabOrder.objects.get(lab_number=item.lab_number)
                lbo.coating_sku = 'HMC'
                lbo.coating_name = 'HMC'
                lbo.comments_inner +='|System Changed HC to HMC'
                lbo.save()

        else:
            return 'NULL'


        return file_name

    def get_weekly_report_data(self):
        return None

    def get_data(self, sql):
        try:
            with connections['pg_oms_query'].cursor() as cursor:
                cursor.execute(sql)
                titles = self.get_title_list(cursor.description)
                items = namedtuplefetchall(cursor)

            data = {}
            data['titles'] = titles
            data['items'] = items

            return data
        except Exception as ex:
            logging.error(str(ex))
            return None

    def _get_yesterday(self):
        date = {}
        now = datetime.datetime.now()
        yesterday = now - timedelta(days=1)
        logging.debug(yesterday)

        date_str = yesterday.strftime("%Y-%m-%d")

        date_start = date_str + ' 00:00:00'
        date_end = date_str + ' 23:59:59'
        date['date_str'] = date_str
        date['date_start'] = date_start
        date['date_end'] = date_end

        return date

    def get_yesterday_sql(self):
        date = self._get_yesterday()
        date_str = date['date_str']
        date_start = date_str + ' 00:00:00'
        date_end = date_str + ' 23:59:59'

        now = datetime.datetime.now()
        date_time = now.strftime("%Y-%m-%d %H-%m-%s")

        data = {}
        # 镜片收货汇总
        sql_sums = """
            -- 非自有库存镜片收货汇总
        """
        # sql_sums = sql_sums % (date_start, date_end)
        # data['sums'] = sql_sums

        # logging.debug('sums')

        sql = """
        select id,lab_number,frame,lens_sku,coating_sku,status,
        vendor,workshop,create_at as created_at,user_name
        from oms_laborder where coating_sku='HC' AND lens_sku<>'KD56' limit 1000;
        """

        data['lab_job_hc'] = sql

        data['title_parameters'] = date_time
        logging.debug('title_parameters')

        return data

    def get_last_week_sql(self):
        pass

    def get_last_month_sql(self):
        pass

    # 根据游标描述获取Title
    def get_title_list(self, cursor_description):
        data_dict = []
        for field in cursor_description:
            data_dict.append(field[0])
        return data_dict

    # 转换列表类型
    def convert_data_type(self, data):
        list_data = []
        for item in data:
            ll = []
            for k in item:
                if type(item[k]) == decimal.Decimal:
                    ll.append(round(float(item[k]), 2))
                else:
                    ll.append(item[k])
            list_data.append(ll)
        return list_data

    # Write to Excel
    def write2xl(self, ew, title_list, data_list, sheet_name):
        logging.debug('method: write2xl')

        logging.debug(title_list)

        df = pd.DataFrame(columns=title_list, data=data_list)
        defaults = {'font': utils.fonts.aharoni, 'font_size': 14}
        list_sf = StyleFrame(df, styler_obj=Styler(**defaults))
        # Style the headers of the table
        header_style = Styler(bold=True, font_size=18)
        list_sf.apply_headers_style(styler_obj=header_style)
        # Change the columns width and the rows height
        list_sf.set_column_width(columns=list_sf.columns, width=30)
        list_sf.set_row_height(rows=list_sf.row_indexes, height=25)

        # list_sf.apply_column_style(cols_to_style=title_list)

        list_sf.to_excel(excel_writer=ew, sheet_name=sheet_name,
                         # Add filters in row 0 to each column.
                         row_to_add_filters=0,
                         # Freeze the columns before column 'A' (=None) and rows above '2' (=1),
                         # columns_and_rows_to_freeze='A2'
                         ).save()

    # Sending Dingdign Message
    def ding_msg(self, file_name, txt_body):
        try:
            logging.debug('Sending ding message ....')

            E_AppKey = 'dingl4ffi9i8c4zl2m41'
            E_AppSecret = 'VZ7L2ue_Fasulcv40CfrmBdLmKLDAgwLWQPDEr1Fd3PlB2TM5caVVjIGpwbYlaRr'
            AgentId = '300734750'
            CorpId = 'ding1876ffde971a32eb'
            client = AppKeyClient(CorpId, E_AppKey, E_AppSecret)  # 新 access_token 获取方式

            headers = {}
            data = {}
            url = 'https://oapi.dingtalk.com/media/upload?access_token=' + client.access_token + '&type=file'
            """
                :param files: (optional) Dictionary of ``'name': file-like-objects`` (or ``{'name': file-tuple}``) for multipart encoding upload.
                ``file-tuple`` can be a 2-tuple ``('filename', fileobj)``, 3-tuple ``('filename', fileobj, 'content_type')``
                or a 4-tuple ``('filename', fileobj, 'content_type', custom_headers)``, where ``'content-type'`` is a string
                defining the content type of the given file and ``custom_headers`` a dict-like object containing additional headers
                to add for the file.
            """
            data['media'] = (file_name, open(r'%s' % file_name, 'rb').read())
            encode_data = encode_multipart_formdata(data)
            data = encode_data[0]
            headers['Content-Type'] = encode_data[1]
            r = requests.post(url, headers=headers, data=data)
            k = json.loads(r.text)

            t1 = message.TextBody(txt_body)
            t2 = message.FileBody(k.get('media_id'))
            # keep touch
            sel_chat_id = 'chat1fa6ffa170a762c040b5f0cc042ade7c'  # keep touch
            sel_chat_id = 'chat596d30e5625ae08b5fd85ebe29b00091'  # IT 周会
            sel_chat_id = 'chat8b63a87cf13980d9ca1e294b946d2c4f'  # 财务群
            sel_chat_id = 'chatcc42fa7d5b85ba68c6ff88467a3b6dd4'  # 客服&生产
            client.chat.send(sel_chat_id, t1)
            client.chat.send(sel_chat_id, t2)

            logging.debug('Ding message has been sent ....')
        except Exception as ex:
            logging.error(str(ex))
