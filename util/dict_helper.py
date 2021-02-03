# -*- coding: utf-8 -*-

class dict_helper:
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


# dict 转 obj
class DictToObj(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [DictToObj(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, DictToObj(b) if isinstance(b, dict) else b)



LAB_STATUS ={
    '':'新订单',
    'REQUEST_NOTES':'出库申请',
    'FRAME_OUTBOUND':'镜架出库',
    'PRINT_DATE':'单证打印',
    'LENS_OUTBOUND':'镜片出库',
    'LENS_REGISTRATION':'来片登记',
    'LENS_RETURN':'镜片退货',
    'LENS_RECEIVE':'镜片收货',
    'ASSEMBLING': '待装配',
    'ASSEMBLED': '装配完成',
    'GLASSES_RECEIVE':'成镜收货',
    'FINAL_INSPECTION': '终检',
    'FINAL_INSPECTION_YES':'终检合格',
    'FINAL_INSPECTION_NO': '终检不合格',
    'GLASSES_RETURN': '成镜返工',
    'COLLECTION': '归集',
    'PRE_DELIVERY': '预发货',
    'PICKING': '已拣配',
    'ORDER_MATCH': '订单配对',
    'BOXING':'装箱',
    'SHIPPING': '已发货',
    'ONHOLD':'暂停',
    'CANCELLED': '取消',
    'REDO':'重做',
    'R2HOLD':'申请暂停',
    'R2CANCEL':'申请取消',
    'CLOSED': '关闭'
}
def format_str(content):
    if content == '' or content is None:
        return '----'
    else:
        return content
