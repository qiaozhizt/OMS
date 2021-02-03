# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
import logging
from oms.controllers.wx_meta_purchase_controller import wx_meta_purchase_controller
from vendor.models import WxMetaProductRelationship


class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('start ....')
        wx_pur_ctrl = wx_meta_purchase_controller()
        res = wx_pur_ctrl.list_wx_meta_products()
        for item in res['data']:
            wx_meta = WxMetaProductRelationship()
            wx_meta.cylStart = item['cylStart'] if item['cylStart'] else 0
            wx_meta.dl = item['dl'] if item['dl'] else ''
            wx_meta.lenInputType = item['lenInputType'] if item['lenInputType'] else ''
            wx_meta.addEnd = item['addEnd'] if item['addEnd'] else 0
            wx_meta.brand = item['brand'] if item['brand'] else ''
            wx_meta.sphEnd = item['sphEnd'] if item['sphEnd'] else 0
            wx_meta.rate = item['rate'] if item['rate'] else ''
            wx_meta.price = item['price'] if item['price'] else 0
            wx_meta.sphStart = item['sphStart'] if item['sphStart'] else 0
            wx_meta.lentype = item['lentype'] if item['lentype'] else ''
            wx_meta.addStart = item['addStart'] if item['addStart'] else 0
            wx_meta.cylEnd = item['cylEnd'] if item['cylEnd'] else 0
            wx_meta.zsl = item['zsl'] if item['zsl'] else ''
            wx_meta.isLr = item['isLr'] if item['isLr'] else ''
            wx_meta.defName = item['defName'] if item['defName'] else ''
            wx_meta.customerId = item['customerId'] if item['customerId'] else ''
            wx_meta.productName = item['productName'] if item['productName'] else ''
            wx_meta.productId = item['productId'] if item['productId'] else ''
            wx_meta.sku = ''
            wx_meta.save()
        logging.critical('所有操作成功结束 ....')
