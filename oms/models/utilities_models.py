# -*- coding: utf-8 -*-
import simplejson as json
import qrcode
from os import path
import os
from barcode.writer import ImageWriter
from barcode.codex import Code39
from pygame.locals import *
from hubarcode.code128 import Code128Encoder
import time
from pg_oms.settings import *
import requests
import base64

class utilities:

    @staticmethod
    def convert_to_dicts(objs):
        """

        :param objs:
        :return:

        把对象列表转换为字典列表
        """

        obj_arr = []

        for o in objs:
            # 把Object对象转换成Dict
            dict = {}
            dict.update(o.__dict__)
            dict.pop("_state", None)  # 去除掉多余的字段
            obj_arr.append(dict)

        return obj_arr

    @staticmethod
    def convert_to_dict(obj):
        """

        :param obj:
        :return:

        把对象转换为DICT
        """
        dict = {}
        dict.update(obj.__dict__)
        dict.pop("_state", None)
        return dict

    # def convert_to_json(obj):
    #     return json.dumps(self.convert_to_dicts(obj))
    # 生成二维码方法
    @staticmethod
    def createQR(lab_number):
        d = path.dirname(__file__)
        parent_path = os.path.dirname(d)

        parent_path = parent_path.replace("\\", "/")
        print parent_path
        qr = qrcode.QRCode(version=1,
                           error_correction=qrcode.constants.ERROR_CORRECT_L,
                           box_size=8,
                           border=8,
                           )
        qr.add_data(lab_number)
        qr.make(fit=True)
        img = qr.make_image()
        img.save(parent_path + "/static/scan/qr/" + lab_number + '.png')

    # 生成code39方法
    @staticmethod
    def createC39(lab_number):
        d = path.dirname(__file__)
        parent_path = os.path.dirname(d)
        parent_path = parent_path.replace("\\", "/")
        imagewriter = ImageWriter()
        # add_checksum : Boolean   Add the checksum to code or not (default: True)
        ean = Code39(lab_number, writer=imagewriter, add_checksum=False)
        # 不需要写后缀，ImageWriter初始化方法中默认self.format = 'PNG'
        ean.save(parent_path + '/static/scan/c39/' + lab_number)

    # 生成c128
    @staticmethod
    def createC128(lab_number, create_date='', file_name='barcode'):
        try:
            d = path.dirname(__file__)
            parent_path = os.path.dirname(d)
            parent_path = parent_path.replace("\\", "/")
            file_name = file_name

            # 1 生成条形码
            text = lab_number
            if create_date:
                date = create_date.strftime('%Y-%m-%d')
            else:
                date = datetime.datetime.now().strftime('%Y-%m-%d')

            response_data = save_barcode(date, file_name, text)
            if response_data['code'] == 0:
                return response_data['data']
            else:
                return ''
        except Exception as e:
            new_img_src = ''
            return new_img_src

    @staticmethod
    def struct_time(dt):
        return time.strptime(dt, "%Y-%m-%d %H:%M:%S")

    @staticmethod
    def struct_day(dt):
        return time.strptime(dt, "%Y-%m-%d")

    @staticmethod
    def generate_code128(lab, file_name='barcode'):
        # 1 生成条形码
        if not lab.c128_path:
            text = str("%s%s" % (BAR_CODE_PREFIX, lab.id))
            date = lab.create_at.strftime('%Y-%m-%d')
            response_data = save_barcode(date, file_name, text)
            if response_data['code'] == 0:
                lab.c128_path = response_data['data']
                lab.save()
                return True
            else:
                return False
        else:
            return False


import json
import datetime
import decimal

class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, datetime.date):
            return obj.strftime("%Y-%m-%d")
        elif isinstance(obj,decimal.Decimal):
            return str(obj)
        else:
            return json.JSONEncoder.default(self, obj)


def save_barcode(date, file_name, text):
    rm = {}
    try:
        encoder = Code128Encoder(text, options={"ttf_fontsize": 12,
                                                "bottom_border": 15,
                                                "height": 50,
                                                "label_border": 2})
        date_list = date.split("-")
        year = date_list[0]
        month = date_list[1]
        day = date_list[2]
        make_dir_year = SSH_MEDIA_SERVER.get('LOCAL_MEDIA_BASE') + file_name + "/" + year
        make_dir_month = SSH_MEDIA_SERVER.get('LOCAL_MEDIA_BASE') + file_name + "/" + year + "/" + month
        make_dir_day = SSH_MEDIA_SERVER.get('LOCAL_MEDIA_BASE') + file_name + "/" + year + "/" + month + "/" + day
        if not os.path.exists(make_dir_year):
            os.makedirs(make_dir_day)

        if not os.path.exists(make_dir_month):
            os.makedirs(make_dir_day)

        if not os.path.exists(make_dir_day):
            os.makedirs(make_dir_day)
        img_src = make_dir_day + "/" + text + ".png"
        encoder.save(img_src, bar_width=1)
        new_img_src = "media/" + file_name + "/" + year + "/" + month + "/" + day + "/" + text + ".png"
        rm['code'] = 0
        rm['data'] = new_img_src
        return rm
    except Exception as e:
        logging.debug('save_barcode Exception: %s' % str(e))
        rm['code'] = -1
        rm['data'] = ''
        return rm