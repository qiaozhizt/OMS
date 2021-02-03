# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from oms.views import *
import logging
import datetime
from pg_oms.settings import WX_PURCHASE
from vendor.models import WxOrderStatus


class Command(BaseCommand):
    def handle(self, *args, **options):
        url = WX_PURCHASE.get('WX_ORDER_STATUS')
        headers = {'Content-Type': 'application/json'}
        try:
            # 获取待装配,出库申请，镜架出库,镜片生产的订单
            lbos = LabOrder.objects.filter(vendor='9', status__in=['ASSEMBLING', 'FRAME_OUTBOUND', 'REQUEST_NOTES', 'GLASSES_RETURN', 'PRINT_DATE'])
            for lbo in lbos:
                logging.debug('-------------------------------------------------------------')
                logging.debug('Lab Number=%s' % lbo.lab_number)
                if lbo.vendor_order_reference:
                    time.sleep(1)
                    url_do = url + '?AccountId=1&OrderID=' + lbo.vendor_order_reference
                    logging.debug('URL=%s' % url_do)
                    # 设置重连次数
                    requests.adapters.DEFAULT_RETRIES = 5
                    s = requests.session()
                    # 设置连接活跃状态为False
                    s.keep_alive = False
                    # 请求伟星接口查询订单状态
                    req = requests.get(url_do, headers=headers)  # 作为data参数传递到Request对象中
                    resp = req.text
                    respjs = json.loads(resp)
                    if respjs['Success']:
                        # 查询最新一条状态
                        jb_tk_rxs = WxOrderStatus.objects.filter(order_number=lbo.lab_number).order_by('-id')
                        if jb_tk_rxs.count() > 0:
                            jb_tk_rx = jb_tk_rxs[0]
                            if not jb_tk_rx.status_value == respjs['Data']['Status']:
                                self.save_data(lbo, respjs)
                                logging.debug('请求成功，写入Tracking，Data=%s' % respjs['Data'])
                            else:
                                logging.debug('状态与上一次状态相同')
                        else:
                            self.save_data(lbo, respjs)
                    else:
                        logging.debug('请求出错')
                else:
                    logging.debug('车房单号为空,不请求')
                logging.debug('-------------------------------------------------------------')
        except Exception as e:
            logging.debug(e)
        finally:
            # 关闭请求  释放内存
            req.close()
            del(req)

    def save_data(self, lbo, respjs):
        try:
            now_date = datetime.datetime.now()
            wxorderstatus = WxOrderStatus()
            wxorderstatus.order_number = lbo.lab_number
            wxorderstatus.reference_code = lbo.vendor_order_reference
            wxorderstatus.status_code = respjs['Data']['TrayNo'] if respjs['Data']['TrayNo'] else ''
            wxorderstatus.status_value = respjs['Data']['Status']
            wxorderstatus.status_updated_at = now_date
            wxorderstatus.save()
        except Exception as e:
            logging.debug(e)
