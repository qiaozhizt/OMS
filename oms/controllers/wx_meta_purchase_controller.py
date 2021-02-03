# -*- coding: utf-8 -*-
import logging
import simplejson as json
import time
import requests
from api.controllers.tracking_controllers import tracking_lab_order_controller
from vendor.models import WxMetaProductRelationship, LensSpecmap
from pg_oms.settings import WX_META_SERVICE, WX_META_PURCHASE
from oms.models.order_models import PurchaseOrderRecords

class wx_meta_purchase_controller:
    '''
    WX Meta Purchase Controller class
    '''
    def __init__(self):
        self.orderType = 'meta'
        self.deliverType = '顺丰寄付'                    #快递方式指定圆通
        self.customerLinkman = '李莲英'              #联系人
        self.customerTel = '15518639392'            #联系电话
        self.customerProvince ='上海市'              #省
        self.customerCity = '上海市'                 #市
        self.customerCounty = '奉贤区'                    #区
        self.customerAddress='大叶公路4601号伟星工业园' #地址

        self.name = 'A100311'                       # 智镜客户码 固定的 A100311
        self.pwd  = 'zhijin123'                     # 获取令牌密码

        self.host = WX_META_SERVICE if isinstance(WX_META_SERVICE, str) else WX_META_SERVICE[0]#伟星系统地址，写入配置文件
        self.token_url = WX_META_PURCHASE.get('TOKEN_URL') #'/all/account/login'#获取令牌URL
        self.wx_meta_prd_url = WX_META_PURCHASE.get('WX_META_PRD_URL') #'/api/product/listCustomerProducts'  #获取现片产品清单
        self.add_order_url = WX_META_PURCHASE.get('ADD_ORDER_URL') #'/api/order/addOrder'添加订单URL
        self.order_status_url= WX_META_PURCHASE.get('ORDER_STATUS_URL')#'/api/order/getOrderStatus'   #获取订单状态URL

        #库存片产品对应关系，需写入对应关系表中
        self.meta_product_relation = {
            'KD56L': '00000000000000008736',
            'KD56': '00000000000000002750',
            'KDB56-C': '00000000000000002443',
            'KD61L': '00000000000000004648',
            'KDB61-H-SHMC': '00000000000000004048',
            'KD61': '00000000000000002549',

        }
    # 获取令牌
    '''
        ### 参数
        * `name`：名字
        * `pwd`：密码
    '''
    def get_headers(self,content_type='application/json'):
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded;charset=utf-8'
        }
        try:
            url = self.host + self.token_url + "?name=%s&pwd=%s"%(self.name,self.pwd)
            logging.debug(url)
            result = requests.post(url, headers=headers, timeout=60)
            account = json.loads(result.text)
            if account['code'] == '200' and account['map']['data']['token']:
                headers = {
                    "Content-Type": content_type,
                    "X-Auth-Token": account['map']['data']['token']
                }
                return {"code":0,"headers":headers,"msg":"成功获取token"}
            else:
                return {"code":-1,"token":"","msg":"伟星接口返回信息变化"}
        except Exception as e:
            return {"code": -1, "token": "", "msg": "get token failed%s"%str(e)}

    #获取现片产品列表
    '''
        /api/product/listCustomerProducts
        ### 参数
        无

        ### 响应
        ```json
        {
            "success": true,
            "code": "200",
            "message": null,
            "map": {
                "data": [{
                    productId: `'xxx'`, 销售品名id
                        brand: `'xxx'`, 品牌
        lenType: `'xxx'`, 光型
        sphStart: `0.00`, 球镜起始值
        sphEnd: `0.00`, 球镜结束值
        cylStart: `0.00`, 柱镜起始值
        cylEnd: `0.00`, 柱镜结束值
        addStart: `0.00`, 加光起始值
        addEnd: `0.00`, 加光结束值

        productName: `'xxx'`, 销售品名
        zsl: `'xxx'`, 折射率
        dl: `'xxx'`, 大类
        price: `100.0`, 单价
        rate: `1.0`, 折扣
        }]
        }
        }
        ```
    '''
    def list_wx_meta_products(self):
        content_type = 'application/x-www-form-urlencoded;'
        try:
            result = self.get_headers(content_type)
            logging.debug(result)
            if (result['code'] == -1):  # 返回出错信息
                return result
            headers = result['headers']
            url = self.host + self.wx_meta_prd_url
            result = requests.post(url, headers=headers, timeout=60)
            response = json.loads(result.text)
            if response['code'] == "200":
                return {"code": 0, "data": response['map']['data'], "msg": "success"}
            else:
                return {"code": -1, "msg": response['message']}
        except Exception as e:
            return {"code": -1, "msg": "获取车房列表失败，异常信息：%s" % str(e)}




        #生成订单
    '''
        * `addOrderDTOStr`: json字符串，json格式：
        * orderType: 订单类型,`meta/house`分别表示现片/车房
        * apiOrderNo: 第三方订单号
        * deliveryDate: `'yyyy-MM-dd'`,要求发货日期
        * deliverType: `'圆通'`,快递方式
        * customerLinkman: `'张三'`,联系人
        * customerTel: `'152xxxx'`,联系电话
        * customerProvince: `'浙江省'`,省
        * customerCity: `'台州市'`,市
        * customerCounty: `'xxx'`,区
        * customerAddress: `'xxx'`,地址
        * note: `'xxx'`,备注

        * items: 订单明细列表
            * type: `'meta'`, 值为meta/house/frame,分别代表现片/车房/镜架
            * productId: `'J123'`,销售品名id
            * quantity: `1`,数量
            * brand: `'白包装'`,品牌
            * lr: `'l'`,左右眼
            * sphval: `'1.0'`,球镜
            * cylval: `'1.0'`,柱镜
            * addval: `'1.0'`,加光
            * lentype: `'近视'`,光型
            * axis: `1`,光轴
            * cbase: `'1'`,基弯
            * coloring：`'wf-01'`,染色内容
            * prismA：`'1'`,棱镜a
            * directionA：`'内'`,方向a
            * prismB：`'1'`,棱镜b
            * directionB：`'上'`,方向b
            * isAsse：`'Y'`,是否装配
            * isCut：`'N'`,是否割边
            * framePd：`'65'`,瞳距
            * frameIpd：`''`,近用瞳距
            * framePh：`''`,瞳高
            * glassDistance：`''`,眼距
            * frontAngle：`''`,前倾角
            * moveIn：`''`,移心-内移
            * moveOut：`''`,移心-外移
            * processes: `{'镀膜': '蓝光'}`,json格式,`工艺类型:工艺ID`的映射

            ### 响应
            ```json
            {
                "success": true,
                "code": "200",
                "message": null,
                "map": {
                    "data": null
                }
            }
            ```
    '''
    def add_meta_order(self, dict_data, delveryDate="", brand='白包装', isAsse="N", isCut="N"):
        result = self.get_headers()
        if(result['code'] == -1):    #返回出错信息
            return result
        headers = result['headers']
        try:
            wx_meta_lens = LensSpecmap.objects.filter(inner_code=dict_data.get('rsku'), active='ACTIVE', vendor=dict_data.get('vendor'))
            #wx_meta_lens = WxMetaProductRelationship.objects.filter(sku=dict_data.get('rsku'))
            if len(wx_meta_lens) == 0 or len(wx_meta_lens) > 1:
                return {"code": -1, "data": '', "msg": "未找到对应关系"}
            wx_meta_len = wx_meta_lens[0]
            l_product_id = wx_meta_len.outer_code
            r_product_id = wx_meta_len.outer_code

            if(not delveryDate): #默认要求当天发货
                delveryDate = time.strftime("%Y-%m-%d", time.localtime())

            order_dict = {
                            "orderType": self.orderType,#默认现片
                            "apiOrderNo": dict_data.get('order_number', ''),
                            "deliveryDate": delveryDate,
                            "deliverType": self.deliverType,
                            "customerLinkman": self.customerLinkman,
                            "customerTel": self.customerTel,
                            "customerProvince": self.customerProvince,
                            "customerCity": self.customerCity,
                            "customerCounty":self.customerCounty,
                            "customerAddress": self.customerAddress,
                            "note": dict_data.get('comments', ''),
                            "items": [
                                {
                                    "type": self.orderType,
                                    "productId": l_product_id,
                                    "quantity": 1,
                                    "brand": brand,
                                    "lr": "l",
                                    "sphval": dict_data.get('lsph', '0'),
                                    "cylval": dict_data.get('lcyl', '0'),
                                    "lentype": dict_data.get('l_lens_type', ''),
                                    "axis": dict_data.get('laxis', '0'),
                                    "addval": "0.00",
                                    "cbase": "",
                                    "coloring": "",
                                    "prismA": 0,
                                    "directionA": "",
                                    "prismB": 0,
                                    "directionB": "",
                                    "isAsse": isAsse, #是否装配
                                    "isCut": isCut,  #切边
                                    "framePd": 0,
                                    "frameIpd": "",
                                    "framePh": "",
                                    "glassDistance": "",
                                    "frontAngle": "", #前倾角 无
                                    "moveIn": "",
                                    "moveOut": "",
                                    "processes": {} #工艺，无
                                },
                                {
                                    "type": self.orderType,
                                    "productId": r_product_id,
                                    "quantity": 1,
                                    "brand": brand,
                                    "lr": "r",
                                    "sphval": dict_data.get('rsph', '0'),
                                    "cylval": dict_data.get('rcyl', '0'),
                                    "lentype": dict_data.get('r_lens_type', ''),
                                    "axis": dict_data.get('raxis', '0'),
                                    "addval": "0.00",
                                    "cbase": "",
                                    "coloring": "",
                                    "prismA": 0,
                                    "directionA": "",
                                    "prismB": 0,
                                    "directionB": "",
                                    "isAsse": isAsse,  # 是否装配
                                    "isCut": isCut,  # 切边
                                    "framePd": 0,
                                    "frameIpd": "",
                                    "framePh": "",
                                    "glassDistance": "",
                                    "frontAngle": "",  # 前倾角 无
                                    "moveIn": "",
                                    "moveOut": "",
                                    "processes": {}  # 工艺，无
                                },
                            ]
                        }
            #{"code":"500","map":{"data":null},"message":"没有价格！产品ID：00000000000000008736 品牌：白包装 光型：近视 球：1 柱：2 加光：0","success":false}
            url = self.host + self.add_order_url
            result = requests.post(url, data=json.dumps(order_dict), headers=headers, timeout=60)
            response = json.loads(result.text)
            if response['code'] == "200":
                # 存储下单信息
                purchase_order_records = PurchaseOrderRecords.objects.filter(lab_number=dict_data.get('order_number', ''))
                if len(purchase_order_records) > 0:
                    pur_order_records = purchase_order_records[0]
                    pur_order_records.order_data = json.dumps(order_dict)
                    pur_order_records.vendor = '10'
                    pur_order_records.save()
                else:
                    pur_order_records = PurchaseOrderRecords()
                    pur_order_records.lab_number = dict_data.get('order_number', '')
                    pur_order_records.order_data = json.dumps(order_dict)
                    pur_order_records.vendor = '10'
                    pur_order_records.save()
                return {"code": 0, "data": response['map']['data'], "msg": "success!"}
            else:
                return {"code": -1, "data": response['map']['data'], "msg": response['message']}
        except Exception as e:
            return {"code": -1, "data": "", "msg": "生成订单失败，异常信息：%s"%str(e)}

    #根据伟星订单号获取伟星订单生产状态
    '''
    ### 参数
        * `orderNo`: 订单号(不是订单ID)

        ### 响应
        ```json
        {
            "success": true,
            "code": "200",
            "message": null,
            "map": {
                "data": {
                    "status": "1",
                    "deliverNo": "123",
                    "deliverCompany": "圆通"
                }
            }
        }
        ```

        #### 订单状态
        * "-1": 已删除
        * "0": 待引入
        * "1": 待审核
        * "23": 待确认
        * "25": 已终止
        * "27": 已取消
        * "30": 生产中
        * "35": 割边处理
        * "37": 单证打印
        * "38": 部分发货
        * "40": 完成
    '''
    def getOrderStatus(self,orderNo):
        if(orderNo == ""):
            return {"code": -1,"msg": "订单号不能为空"}
        content_type ='application/x-www-form-urlencoded;'
        try:
            result = self.get_headers(content_type)
            logging.debug(result)
            if (result['code'] == -1):  # 返回出错信息
                return result
            headers = result['headers']
            url = self.host + self.order_status_url + "?orderNo=%s"%orderNo
            result = requests.post(url, headers=headers, timeout=60)
            response = json.loads(result.text)
            if response['code'] == "200":
                return {"code":0,"data":response['map']['data'],"msg":"success"}
            else:
                return {"code":-1,"msg":response['message']}
        except Exception as e:
            return {"code": -1, "msg": "获取订单状态错误，异常信息：%s"%str(e)}

    #封装数据
    def pack_request_value(self, lab):
        data_dict = {}
        try:
            if float(lab.od_sph) <= 0:
                r_lens_type = '近视'
            else:
                r_lens_type = '老花'

            if float(lab.os_sph) <= 0:
                l_lens_type = '近视'
            else:
                l_lens_type = '老花'

            if int(lab.vendor) > 9:
                act_lens_sku = lab.act_lens_sku[3:]
            else:
                act_lens_sku = lab.act_lens_sku[2:]

            data_dict['order_number'] = lab.lab_number
            data_dict['vendor'] = lab.vendor
            data_dict['rsku'] = act_lens_sku
            data_dict['rsph'] = lab.od_sph
            data_dict['rcyl'] = lab.od_cyl
            data_dict['raxis'] = lab.od_axis
            data_dict['r_lens_type'] = r_lens_type

            data_dict['lsku'] = act_lens_sku
            data_dict['lsph'] = lab.os_sph
            data_dict['lcyl'] = lab.os_cyl
            data_dict['laxis'] = lab.os_axis
            data_dict['l_lens_type'] = l_lens_type
            data_dict['comments'] = lab.comments
            return data_dict
        except Exception as e:
            return data_dict

    #处理返回结果
    def analysis_result(self, request, lbo, purchase_order, res):
        stat_dict = {}
        try:
            if res['code'] == 0:
                purchase_order.vendor_order_reference = res['data']['orderNo']
                purchase_order.save()
                lbo.vendor_order_reference = res['data']['orderNo']
                lbo.save()
                # 记录日志
                tloc = tracking_lab_order_controller()
                tloc.tracking(lbo, request.user, 'LENS_PURCHASE', '镜片采购',
                              res['data']['orderNo'])
                stat_dict[lbo.lab_number] = {'Success': True, 'Message': '下单成功'}
            else:
                stat_dict[lbo.lab_number] = {'Success': False, 'Message': res['msg']}
            return stat_dict
        except Exception as e:
            stat_dict[lbo.lab_number] = {'Success': False, 'Message': e}
            return stat_dict



