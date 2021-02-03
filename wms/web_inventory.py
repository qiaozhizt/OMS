# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import simplejson as json
from .models import *
from util.db_helper import *
import requests
from util.format_helper import *
import logging
from pg_oms.settings import PG_INVENTORY_HOST, BASE_URL
from oms.const import token_data, token_header, token_url


class web_inventory:
    # web_host = "http://beta2.payneglasses.com:8889/"
    web_host = PG_INVENTORY_HOST
    stock_in_web_url= web_host+"inventory/api_receipt_list/"
    stock_out_web_url = web_host+"inventory/api_delivery_list/"
    update_web_struct_info_url = web_host+"inventory/api_update_inventory/"
    mail_url = web_host+"inventory/api_mail/"
    inventory_api_url = web_host + "inventory/api/"
    #获取所有sku的预留数量列表
    def get_reserve_qty(self,lab_sku='',dict=True):
        results = {}
        with connections['default'].cursor() as cursor:
            try:
                # 1.进入pgorder未生成laborder的frame 预留数量
                poi_reservse_qty_sql = "select SUBSTRING(frame,2,7) as frame,quantity from oms_pgorderitem inner join oms_pgorder on oms_pgorderitem.pg_order_entity_id=oms_pgorder.id where oms_pgorder.`status` in('processing','holded') and `is_inlab` =0 "
                #  2.生成laborder，镜架未出库的frame 预留数量
                lab_reservse_qty_sql="select frame,quantity from `oms_laborder` where oms_laborder.status in('',Null,'REQUEST_NOTES')"

                if lab_sku:
                    poi_reservse_qty_sql += " and SUBSTRING(frame,2,7)='%s'"%lab_sku
                    lab_reservse_qty_sql += " and frame='%s'"%lab_sku
                    logging.debug(poi_reservse_qty_sql)

                sql = "select sum(quantity) as quantity,frame from (%s union all  %s )  as reserve group by frame"%(poi_reservse_qty_sql,lab_reservse_qty_sql)
                logging.debug("查询预留库存sql: %s"% sql)

                cursor.execute(sql)
                if dict:
                    return namedtuplefetchall(cursor)
                else:
                    return cursor.fetchall()  #namedtuplefetchall
            except Exception as e:
                logging.debug("查询预留库存sql: %s 时出错：%s" % (sql, e))
                return results

    #批量初始预留数量
    def init_reserve_qty(self):
            args = self.get_reserve_qty(dict=False)
            logging.debug(args)
            logging.debug("***************初始化开始***************")
            with connections['default'].cursor() as cursor:
                try:
                    inventory_struct_sql = "update wms_inventory_struct set reserve_quantity = %s where sku=%s"
                    cursor.fast_executemany = True
                    cursor.executemany(inventory_struct_sql, args)
                    connections['default'].commit()
                except Exception as e:
                    logging.debug("**********初始库存结构预留库存数量出错：%s***************" %e)


    #在原来基础上增加或减少预留数量---暂时没有使用
    def update_reserve_qty(self,sku,qty):
        try:
            invs = inventory_struct.objects.get(sku=sku)
            invs.reserve_quantity +=qty
            invs.save()
        except Exception as e:
            logging.debug("修改预留sku为: %s，数量为：qty 时出错：%s" % (sku,qty,e))

    #网站库存出库
    def web_invs_delivery(self,stock_data):  # 出库
        http_headers = {
            # 'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'
        }
        logging.debug(json.dumps(stock_data))
        try:
            api_response = requests.post(self.stock_out_web_url, data=json.dumps(stock_data), headers=http_headers)
            return  json.loads(api_response.text)
        except Exception, e:
            logging.critical(e)
            return {"code": -1, "message": "接口异常%s"%str(e)}

    # 网站库存入库
    def web_invs_receipt(self,stock_data):
        http_headers = {
            # 'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'
        }
        logging.debug(json.dumps(stock_data))
        try:
            api_response = requests.post(self.stock_in_web_url, data=json.dumps(stock_data), headers=http_headers)
            return json.loads(api_response.text)
        except Exception, e:
            logging.critical(e)
            return {"code": -1, "message": "接口异常%s" % str(e)}
    #邮件接口
    def send_mail(self,data):
        http_headers = {
            # 'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'
        }
        result = False
        try:
            api_response = requests.post(self.mail_url, data=json.dumps(data), headers=http_headers)
            data = json.loads(api_response.text)
            if data.get("code") == 0 or data.get("code") == "0":
                result = True
        except Exception, e:
            logging.critical(e)
        finally:
            return result

    #同步网站结构表
    #入参 1.sku 2.retired 到货日期 安全库存数量
    #这个接口兼容retired，status，以及预计到货日期,格式{"sku":XXXX,"retired":1/0},{"sku":XXXX,"status": "IN_STOCK" or "OUT_OF_STOCK"}
    def update_web_struct_info(self, data):
        http_headers = {
            # 'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'
        }
        result = False
        try:
            logging.debug(json.dumps(data))
            api_response = requests.post(self.update_web_struct_info_url, data=json.dumps(data), headers=http_headers)
            data = json.loads(api_response.text)
            logging.debug(data)
            if data.get("code") == 0 or data.get("code") == "0":
                result = True
        except Exception as e:
            logging.critical(e)
        finally:
            return result

    # 同步数量=逻辑数量-预留数量-安全库存数量
    def syns_base_stock(self):
        #wms_inventory_receipt  入库  类型
        #wms_inventory_delivery 出库
        #逻辑数量 wms_inventory_struct
        #status：UNPUBLISHED（日期）  IN_STOCK  OUT_OF_STOCK  estimate_replenishment_date（预到货时间+7天）
        try:
            result = tuple()
            #1. 查询网站可用数量
            with connections['default'].cursor() as cursor:
                struct_sql = "select 'system' as user_name,status,retired,sku,name as product_name,'FRAME' as product_type,0 as restockable_in_days ,IFNULL(estimate_replenishment_date,NULL) as expected_delivery,IFNULL(lock_quantity,0) as lock_quantity,quantity-reserve_quantity as quantity_on_stock from wms_inventory_struct"
                cursor.execute(struct_sql)
                result = cursor.fetchall()
                logging.debug(result)
                if(len(result)==0):
                    logging.debug("没有要初始化的库存")
                else:
                    logging.debug("~~~~~~~需要初始化的库存有%s条~~~~~~~~~"% str(len(result)))
            # inventory_struct
            #1.清空出入库表(初始化不在入库表插入数据）  2.同步数据
            with connections['web_stock'].cursor() as cursor:
                try:
                    # inventory_struct
                    # 1.清空出入库表,库存结构表（是否要备份）
                    invs_receipt_sql = "delete from inventory_receipt"
                    cursor.execute(invs_receipt_sql)
                    invs_delivery_sql = "delete from inventory_delivery"
                    cursor.execute(invs_delivery_sql)
                    invs_struct_sql = "delete from inventory_struct"
                    cursor.execute(invs_struct_sql)
                    sql = "insert into inventory_struct(user_name,status,retired,sku,product_name,product_type,restockable_in_days,expected_delivery,lock_quantity,quantity_on_stock,created_at,last_modified_at)values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,now(),now())"
                    cursor.fast_executemany = True
                    cursor.executemany(sql, result)
                    connections['web_stock'].commit()
                    logging.debug("~~~~~~~初始化库存%s条~~~~~~~~~"% str(len(result)))
                except Exception as e:
                    logging.debug("初始化化库存出错：%s" % (e))
        except Exception as e:
            logging.debug("初始库存出错：%s" % (e))


    def sync_web_data(self, sku):
        http_headers = {
            #'Authorization': 'Bearer %s' % token,
            'Content-Type': 'application/json'
        }
        try:
            if sku != '':
                api_response = requests.post(self.inventory_api_url, data=json.dumps([sku]), headers=http_headers)
            else:
                api_response = requests.get(self.inventory_api_url, headers=http_headers)
            return json.loads(api_response.text)
        except Exception as e:
            print (e)
            logging.critical(e)
            return {"code": -1, "message": "接口异常%s" % str(e)}
