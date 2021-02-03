# -*- coding: utf-8 -*-

import logging

from util.db_helper import *
from util.response import *
from util.dict_helper import *
from util.format_helper import *
import requests
import simplejson as json

from oms.models.order_models import *
from oms.models.response_models import *
from oms.models.exceptions_models import LabOrderStatusVerifyException
from pg_oms import settings
from vendor.models import lens
from purchase.models import PurchaseOrderChangeLog
from api.controllers.tracking_controllers import tracking_lab_order_controller


class laborder_request_notes_controller:
    def change_vendor(self, request, data):

        logging.debug('laborder_request_notes_controller change_vendor')

        from util.response import response_message
        rm = response_message()

        '''
        1.根据Lab Order的实际镜片查找新的对应Vd对应的SKU;如果有重复的，选择第一条；如果没有对应的，整单调整回滚；
        2.记录当前的所有订单内容；
        3.更新当前出库申请主表和字表的所有vd；
        4.更新对应的所有Lab Order的Vendor；
        5.删除对应vd的采购订单和清单，删除之前备份；
        6.根据新的vd生成采购订单；
        7.对应的系统对接的部分，有没有没有取消订单的接口，需要人工处理。
        '''

        try:

            if request:
                user_id = request.user.id
                user_name = request.user.username
            else:
                user_id = 0
                user_name = 'System'

            # ----------------------------------------
            # 检查
            # 取消和关闭状态的订单排除处理
            # 所有要处理的订单必须是出库申请或镜架出库状态
            # 1.根据Lab Order的实际镜片查找新的对应Vd对应的SKU;如果有重复的，选择第一条；如果没有对应的，整单调整回滚；
            # ----------------------------------------

            lrn_id = data.get('id', '')
            origin_vendor = data.get('origin_vendor', '')
            new_vendor = data.get('new_vendor', '')

            vd_message = 'VD:原[%s]新[%s]' % (origin_vendor, new_vendor)

            logging.debug(vd_message)

            if id == '':
                rm.code = -2
                rm.message = '出库申请单编号不正确'
                return rm

            try:
                lrn = laborder_request_notes.objects.get(id=lrn_id)
            except Exception as ex:
                rm.capture_execption(ex)
                return rm

            items = laborder_request_notes_line.objects.filter(lrn_id=lrn_id)

            for item in items:
                lbo = LabOrder.objects.get(id=item.laborder_entity_id)
                logging.debug('plan:%s act:%s' % (lbo.lens_sku, lbo.act_lens_sku))
                olenss = lens.objects.filter(base_sku=lbo.lens_sku, vendor_code=new_vendor)

                if lbo.status not in ('REQUEST_NOTES', 'FRAME_OUTBOUND',
                                      'CANCELLED', 'R2CANCEL', 'ONHOLD', 'R2HOLD', 'CLOSED'):
                    rm.code = -4
                    rm.message = '只有新订单 出库申请 镜架出库或单证打印的订单 才能转单！ 订单:[%s]当前订单状态是:%s' % \
                                 (lbo.lab_number, lbo.status)
                    logging.debug(rm.message)
                    return rm

                if olenss.count() == 0:
                    rm.code = -3
                    rm.message = '订单号:%s 计划镜片:%s 没有找到对应的供应商产品编码' % (lbo.lab_number, lbo.lens_sku)
                    logging.debug(rm.message)
                    return rm
                else:
                    olens = olenss[0]
                    logging.debug('new_sku:%s new_name:%s' % (olens.sku, olens.name))

            # ----------------------------------------
            # 记录日志
            # ----------------------------------------
            for item in items:
                lbo = LabOrder.objects.get(id=item.laborder_entity_id)
                pocl = PurchaseOrderChangeLog()
                pocl.base_type = item.type
                pocl.base_entity = item.id
                pocl.base_request_notes_id = lrn_id
                pocl.origin_vendor = origin_vendor
                pocl.vendor = new_vendor

                pocl.lab_order_entity = lbo.id
                pocl.lab_number = lbo.lab_number
                pocl.status = lbo.status
                pocl.frame = lbo.frame
                pocl.lens_sku = lbo.lens_sku
                # pocl.lens_name = lbo.lens_name

                pocl.user_id = user_id
                pocl.user_name = user_name

                pocl.save()
                logging.debug('%s Saved ....' % lbo.lab_number)

            # ----------------------------------------
            # 准备开始调整
            # 更新 Lab Order 订单vd和镜片
            # ----------------------------------------
            for item in items:
                lbo = LabOrder.objects.get(id=item.laborder_entity_id)
                logging.debug('plan:%s act:%s' % (lbo.lens_sku, lbo.act_lens_sku))
                olenss = lens.objects.filter(base_sku=lbo.lens_sku, vendor_code=new_vendor)

                if olenss.count() > 0:
                    if lbo.status in ('REQUEST_NOTES', 'FRAME_OUTBOUND'):
                        olens = olenss[0]
                        logging.debug('new_sku:%s new_name:%s' % (olens.sku, olens.name))
                        lbo.vendor = new_vendor
                        lbo.act_lens_sku = olens.sku
                        lbo.act_lens_name = olens.name

                        lbo.save()

            # ----------------------------------------
            # 更新出库申请单
            # ----------------------------------------
            sql = '''
            update oms_laborder_request_notes set vendor=%s where id=%s;
            '''
            sql = sql % (new_vendor, lrn_id)
            DbHelper.execute(sql)

            sql = '''
            update oms_laborder_request_notes_line set vendor=%s where lrn_id=%s;
            '''
            sql = sql % (new_vendor, lrn_id)
            DbHelper.execute(sql)

            # ----------------------------------------
            #  删除采购订单行-表头暂时保留
            # ----------------------------------------
            sql = '''
            delete from oms_laborder_purchase_order_line
            where laborder_id
            in(select laborder_entity_id from oms_laborder_request_notes_line where lrn_id=%s);
            '''
            sql = sql % (lrn_id)
            DbHelper.execute(sql)

            # ----------------------------------------
            #  创建新的采购订单
            # ----------------------------------------
            lopo = laborder_purchase_order()

            lopo.vendor = new_vendor
            lopo.user_id = user_id
            lopo.user_name = user_name
            lopo.save()

            qty = 0
            for item in items:
                lbo = LabOrder.objects.get(id=item.laborder_entity_id)
                logging.debug('plan:%s act:%s' % (lbo.lens_sku, lbo.act_lens_sku))
                olenss = lens.objects.filter(base_sku=lbo.lens_sku, vendor_code=new_vendor)

                if olenss.count() > 0:
                    if lbo.status in ('REQUEST_NOTES', 'FRAME_OUTBOUND'):
                        lopol = laborder_purchase_order_line()
                        lopol.lpo = lopo

                        lopol.laborder_entity = lbo
                        lopol.laborder_id = lbo.id
                        lopol.frame = lbo.frame
                        lopol.lab_number = lbo.lab_number
                        lopol.quantity = lbo.quantity
                        lopol.lens_type = lbo.lens_type
                        lopol.order_date = lbo.order_date
                        lopol.order_created_date = lbo.create_at
                        lopol.purchase_type = 'LENS'
                        lopol.save()

                        # 记录日志 里面加了try
                        tloc = tracking_lab_order_controller()
                        if request:
                            tloc.tracking(lopol.laborder_entity, request.user, 'LENS_REPURCHASE', '镜片重新采购',
                                          vd_message)
                        else:
                            tloc.tracking(lopol.laborder_entity, None, 'LENS_REPURCHASE', '镜片重新采购', vd_message)
                        qty += 1

            lopo.count = qty
            lopo.save()

            rm.message = '此操作已成功'
            logging.debug(rm.message)
        except Exception as ex:
            logging.error(str(ex))
            rm.capture_execption(ex)

        return rm
