# -*- coding: utf-8 -*-
import logging
import time
import codecs
from util.response import response_message
from django.core.management.base import BaseCommand
from wms.models import inventory_initial_channel, inventory_struct, inventory_receipt_channel_controller, channel, product_frame
from oms.models.order_models import LabOrder, PgOrder, PgOrderItem
from pg_oms import settings
#from oms.controllers.pg_order_controller import pg_order_controller
from api.controllers.pgorder_frame_controllers import pgorder_frame_controller

class Command(BaseCommand):
    def handle(self, *args, **options):
        logging.critical('---')
        rm = response_message()
        try:
            #self.initialization_channel()
            self.initialization_inventory_struct()
            self.get_pgorder_item()
            self.get_laborder_item()
            self.synchronization_inventory_initial_channel()
            self.generate_channel_receipt()
        except Exception as e:
            logging.critical("错误：" + str(e))
            rm.capture_execption(e)
            rm.message = '初始化表导入入库表出错'

    def initialization_channel(self):
        """初始化channel"""
        rm = response_message()
        try:
            logging.info("initialization_channel start")
            ch = channel()
            ch.code = "WEBSITE"
            ch.name = "Web Site"
            ch.user_id = 0
            ch.user_name = 'system'
            ch.save()
            logging.info("initialization_channel end")
        except Exception as e:
            logging.critical("error：" + str(e))
            rm.capture_execption(e)
            rm.message = '初始化initialization_channel错误'

    def initialization_inventory_struct(self):
        """初始化inventory_struct下的reserve_quantity为0"""
        rm = response_message()
        try:
            logging.info("initialization_inventory_struct start")
            inventory_struct.objects.all().update(reserve_quantity=0)
            logging.info("initialization_inventory_struct end")
        except Exception as e:
            logging.critical(u"错误：" + str(e))
            rm.capture_execption(e)
            rm.message =u'初始化inventory_struct错误'

    def get_pgorder_item(self):
        """获取pgorder下符合is_inlab为False的条目
        更新inventory_struct的reserve_quantity"""
        rm = response_message()
        try:

            logging.info("get_pgorder_item start")
            pgorders = PgOrder.objects.filter(is_inlab=False)
            file = "wms/data/get_pgorder_item.txt"
            file = settings.RUN_DIR + '/get_pgorder_item_log.txt'
            for item in pgorders:
                logging.info("pgorders id " + str(item.id))
                for pgitem in PgOrderItem.objects.filter(pg_order_entity=item):
                    try:
                        #frame = pgitem.frame[1:8]
                        poc = pgorder_frame_controller()
                        res_rm = poc.get_lab_frame({"pg_frame": item.frame})
                        frame = res_rm.obj['lab_frame']
                        logging.info("pgitem frame " + frame)
                        iis = inventory_struct.objects.get(sku=frame)
                        qty = iis.reserve_quantity + pgitem.quantity
                        iis.reserve_quantity = qty
                        iis.save()
                        logging.info("iis id " + str(iis.id))
                    except Exception as e:
                        with codecs.open(file, 'a', 'utf-8') as w:
                            w.write(u"{0}\t{1}\t{2}\n".format(pgitem.id, pgitem.frame, e))
            logging.info("get_pgorder_item end")
        except Exception as e:
            logging.critical(u"错误：" + str(e))
            rm.capture_execption(e)
            rm.message =u'获取pgorder错误'

    def get_laborder_item(self):
        """获取laborder下符合status='' or NONE or REQUEST_NOTES的条目
        更新inventory_struct的reserve_quantity"""
        rm = response_message()
        try:
            logging.info("get_laborder_item start")
            file = "wms/data/get_laborder_item.txt"
            file = settings.RUN_DIR + '/get_laborder_item_log.txt'
            laborders = LabOrder.objects.filter(status__in=['', None, 'REQUEST_NOTES'])
            for item in laborders:
                try:
                    logging.info("laborders id " + str(item.id))
                    iis = inventory_struct.objects.get(sku=item.frame)
                    qty = iis.reserve_quantity + item.quantity
                    iis.reserve_quantity = qty
                    iis.save()
                except Exception as e:
                    with codecs.open(file, 'a', 'utf-8') as w:
                        w.write(u"{0}\t{1}\t{2}\n".format(item.id, item.frame, e))
            logging.info("get_laborder_item end")
        except Exception as e:
            logging.critical(u"错误：" + str(e))
            rm.capture_execption(e)
            rm.message =u'获取laborder错误'

    def synchronization_inventory_initial_channel(self):
        """同步inventory_struct表中 status == IN_STOCK数据到inventory_initial_channel"""
        rm = response_message()
        try:
            logging.info("synchronization_inventory_initial_channel start")
            #iiss = inventory_struct.objects.filter(status='IN_STOCK')
            iiss = inventory_struct.objects.all()
            for item in iiss:
                qty = item.quantity - item.lock_quantity - item.reserve_quantity
                iic = inventory_initial_channel()
                iic.sku = item.sku
                iic.quantity = qty
                iic.channel_code = 'WEBSITE'
                iic.channel_name = 'Web Site'
                iic.user_id = 0
                iic.user_name = 'system'
                iic.save()
                logging.info("inventory_initial_channel id" + str(iic.id))
            logging.info("synchronization_inventory_initial_channel end")
        except Exception as e:
            logging.critical(u"错误：" + str(e))
            rm.capture_execption(e)
            rm.message =u'同步数据错误'

    def generate_channel_receipt(self):
        """从inventory_initial_channel 生成入库单"""
        rm = response_message()
        try:
            logging.info("generate_channel_receipt start")
            iics = inventory_initial_channel.objects.all()
            for item in iics:
                inventory_receipt_channel_controller().add(None, "20190618", 'WEBSITE', "INIT", item.sku, item.quantity)
                logging.info("generate_channel_receipt sku" + item.sku)
            logging.info("generate_channel_receipt end")
        except Exception as e:
            logging.critical(u"error:" + str(e))
            rm.capture_execption(e)
            rm.message =u'生成入库单错误'
