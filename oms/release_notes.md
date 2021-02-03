# -*- coding: utf-8 -*-

# 2018.05 by guof
# 以后的notes,调整为新消息写在后面

#2018.03.27 by zhai
dashboard页面权限
    DASHBOARD_OPOR   list pgorder comments   pgorder comments 查看权限
    DASHBOARD_OLOR   list laborder comments  laborder comments 查看权限


#2018.03.23 by zhai

维护 ordertrackingreportcs 中pgorder_number和shipping_method 字段    python manage.py order_tracking_report_cs_cron



pgorder和pgorderitem 定时任务   python manage.py generate_order


#2018.03.21 by zhai

维护holiday数据，一年的周日日期      python manage.py holiday_cron

# 2018.03.30 by zhai
维护laborder act_lens_sku 和 act_lens_name     python manage.py laborder_lens_cron


添加权限  pgorder修改保存 laborder的取消，重做，暂停
key               value                               说明
pgorder save        OPOR_SAVE                          pgorder详情修改时的权限
laborder 取消       PORL_CABCELLED                     laborder 点击取消按钮的权限
laborder 暂停       PORL_ONHOLD                        laborder 点击暂停按钮的权限
laborder 重做       PORL_REDO                          laborder 点击重做按钮的权限






# hotfix-1.80220.0320
# 2018.02.22 01.35 by guof.

调整PgOrder的生成Command
去掉了过多的影响性能的logging message
并处理了EntityID的来源
同时减少了算法的循环次数

修正生成LabOrder时的日期计算错误

# hotfix-1.80220.0320

# 2018.02.21 21.01 by guof.
# 在 PgOrder 中增加 is_inlab 字段显示
# 在 LabOrder 中增加：act_lens_sku/act_lens_name/change_reason/lens_delivery_time/has_remake_orders/is_remake_order 等字段
# 执行 Update 语句，将LabOrder 的 Create_at字段更新到lens_delivery_time；将LabOrder的lens_sku/lens_name更新到act_lens_sku/act_lens_name
# 在镜片出库的操作中，将LabOrder的lens_sku/lens_name更新到act_lens_sku/act_lens_name，lens_delivery_time添加为当前时间

# 2018.02.20 14.31
# by guof.
# 修正PgORder生成单号从65开始，到当前订单号结束；
# 对于多生成的订单需要处理
# 修改Pg Order和Lab Order的排序为按Id倒序排序！
# 增加基于 IsEnabled 的筛选；
# 给 Pg Order 增加 Is_InLab字段
# 去掉 Pg Order Item 中的Generate命令


# Lab Order Actions:
# Insert SQL Script:
# 2018.02.20 04.06
# by guof.
# Begin:
# ----------------------------------------------------------------------------------------------------

INSERT INTO `oms_action` (`id`, `type`, `key`, `value`, `object_type`, `description`, `help`, `group`, `sequence`, `create_at`, `update_at`, `is_enabled`)
VALUES
	(1, 'OACS', 'PRINT_DATE', '打印', 'OLOR', NULL, '', 1, 0, '2018-02-19 19:44:26.769120', '2018-02-19 19:44:26.769144', 1),
	(2, 'OACS', 'FRAME_OUTBOUND', '镜架出库', 'OLOR', NULL, '', 1, 10, '2018-02-19 19:44:55.540157', '2018-02-19 19:44:55.540181', 1),
	(3, 'OACS', 'TINT', '染色', 'OLOR', NULL, '', 1, 20, '2018-02-19 19:50:03.394081', '2018-02-19 19:50:03.394104', 1),
	(4, 'OACS', 'RX_LAB', '车房', 'OLOR', NULL, '', 1, 30, '2018-02-19 19:50:25.928306', '2018-02-19 19:50:25.928331', 1),
	(5, 'OACS', 'ADD_HARDENED', '加硬', 'OLOR', NULL, '', 1, 40, '2018-02-19 19:50:52.030701', '2018-02-19 19:50:52.030722', 1),
	(6, 'OACS', 'COATING', '加膜', 'OLOR', NULL, '', 1, 50, '2018-02-19 19:51:31.763862', '2018-02-19 19:51:31.763908', 1),
	(7, 'OACS', 'LENS_RECEIVE', '镜片收货', 'OLOR', NULL, '', 1, 60, '2018-02-19 19:51:55.491094', '2018-02-19 19:51:55.491119', 1),
	(8, 'OACS', 'INITIAL_INSPECTION', '初检', 'OLOR', NULL, '', 1, 70, '2018-02-19 19:52:27.554713', '2018-02-19 19:52:27.554737', 1),
	(9, 'OACS', 'ASSEMBLING', '装配', 'OLOR', NULL, '', 1, 80, '2018-02-19 19:52:50.862482', '2018-02-19 19:52:50.862506', 1),
	(10, 'OACS', 'SHAPING', '整形', 'OLOR', NULL, '', 1, 90, '2018-02-19 19:53:27.003340', '2018-02-19 19:53:27.003373', 1),
	(11, 'OACS', 'FINAL_INSPECTION', '终检', 'OLOR', NULL, '', 1, 100, '2018-02-19 19:53:55.675501', '2018-02-19 19:53:55.675522', 1),
	(12, 'OACS', 'PURGING', '清洗', 'OLOR', NULL, '', 1, 110, '2018-02-19 19:54:30.593960', '2018-02-19 19:54:30.593988', 1),
	(13, 'OACS', 'ORDER_MATCH', '订单配对', 'OLOR', NULL, '', 1, 120, '2018-02-19 19:54:52.022026', '2018-02-19 19:54:52.022051', 1),
	(14, 'OACS', 'PACKAGE', '包装', 'OLOR', NULL, '', 1, 130, '2018-02-19 19:55:12.254911', '2018-02-19 19:55:12.254937', 1),
	(15, 'OACS', 'SHIPPING', '发货', 'OLOR', NULL, '', 1, 140, '2018-02-19 19:55:40.158761', '2018-02-19 19:55:40.158787', 1),
	(16, 'OACS', 'COMPLETE', '完成', 'OLOR', NULL, '', 0, 150, '2018-02-19 19:56:43.174058', '2018-02-19 19:56:43.174081', 1),
	(17, 'OACS', 'ONHOLD', '暂停', 'OLOR', NULL, '', 0, 160, '2018-02-19 19:57:02.824066', '2018-02-19 19:57:02.824089', 1),
	(18, 'OACS', 'CANCELLED', '取消', 'OLOR', NULL, '', 0, 170, '2018-02-19 19:57:23.033248', '2018-02-19 19:57:23.033276', 1),
	(19, 'OACS', 'REDO', '重做', 'OLOR', NULL, '', 0, 180, '2018-02-19 19:57:59.878238', '2018-02-19 19:57:59.878260', 1);

# ----------------------------------------------------------------------------------------------------
# End

lab order action
    在 actions_models 中添加action
    action的顺序是按照sequence从小到大排序，如果要在某两个action中插入一个action sequence的值只要在你要插入的两个action 的sequence之间即可
    KEY :                                VALUE:               SEQUENCE:   group

    OLOR

    PRINT_DATE                          打印                  0            1

    FRAME_OUTBOUND                      镜架出库              10           1

    TINT                                染色                  20           1

    RX_LAB                              车房                  30           1

    ADD_HARDENED                        加硬                  40            1

    COATING                             加膜                  50           1

    LENS_RECEIVE                        镜片收货              60           1

    INITIAL_INSPECTION                  初检                  70           1

    ASSEMBLING                          装配                  80           1

    SHAPING                             整形                  90           1

    FINAL_INSPECTION                    终检                  100          1

    PURGING                             清洗                  110          1

    ORDER_MATCH                         订单配对              120          1

    PACKAGE                             包装                  130          1

    SHIPPING                            发货                  140          1

    COMPLETE                            完成                  150          0

    ONHOLD                              暂停                  160          0

    CANCELLED                           取消                  170          0

    REDO                                重做                  180          0

oms系统权限说明

    KEY                                 VALUE                            说明

    DASHBOARD_NAV                       Dashboard                      Dashboard一级导航权限

    PGORDER_NAV                         Pg Orders                      Pg Orders一级导航权限
       NMOL_VIEW                        New Mg Order List              Pg Orders 导航下的 New Mg Order List二级导航权限
       MOL_VIEW                         Mg Order List                  Pg Orders 导航下的 Mg Order List二级导航权限
       GO_VIEW                          Generate Orders                New Mg Order List 导航下的生成pgorder的权限
       OTRC_VIEW                        Order Tracking Report CS       Pg Orders 导航下的 Order Tracking Report CS二级导航权限
       POL_VIEW                         PgOrder List                   Pg Orders 导航下的 PgOrder List二级导航shipment按钮权限


    LABORDER_NAV                         Lab Orders                    Lab Orders一级导航权限
      OLOR_VIEW                          Lab Order                     Lab Orders 导航下的 Lab Order二级 导航权限
      OTRE_VIEW                          Order Tracking Report         Lab Orders 导航下的 Order Tracking Report二级 导航权限
      OA_VIEW                            Order Address                 Lab Orders 导航下的 Order Address二级 导航权限



    SHIP_NAV                            Shipments                      Shipments一级导航的权限
      OA_VIEW                           Order Address                  Shipments 导航下的 Order Address二级 导航权限





    LAB_ORDER_LIST_DETAIL_BUTTON

            ACT_PRINT_DATE                          打印权限

            ACT_FRAME_OUTBOUND                      镜架出库权限

            ACT_TINT                                染色权限

            ACT_RX_LAB                              车房权限

            ACT_ADD_HARDENED                        加硬权限

            ACT_COATING                             加膜权限

            ACT_LENS_RECEIVE                        镜片收货权限

            ACT_INITIAL_INSPECTION                  初检权限

            ACT_ASSEMBLING                          装配权限

            ACT_SHAPING                             整形权限

            ACT_FINAL_INSPECTION                    终检权限

            ACT_PURGING                             清洗权限

            ACT_ORDER_MATCH                         订单配对权限

            ACT_PACKAGE                             包装权限

            ACT_SHIPPING                            发货权限

            ACT_COMPLETE                            完成权限

            ACT_ESTIMATED_DATE                      预计完成时间权限

            ACT_CANCEL_HOLD                         取消暂停权限

            ACT_ONHOLD                               暂停权限

            ACT_CANCELLED                            取消权限

            ACT_REDO                                 重做权限

            ACT_COMMENT                              添加评论权限

            ACT_PRINTORDER                           打印订单权限


2018.04.08 by zhai
laborder中添加 dia_1和dia_2两个字段
生成laborder时请求url在settings中设置  CALCULATE_DIAMETER_URL


2018.04.20 by zhai
发送时间需在setting文件中设置
PUSH_DATE_URL = 'https://beta.payneglasses.com/rest/default/'

#2018.05.02 by zhai
在settings中设置
USERNAME = "Api"
PASSWORD = "cZHY0TSSkBdIIqYy"

# 2018.05.22 by guof.
需要在settings中增加如下字段
MG_ROOT_URL='https://test.kyoye.com'
PRODUCT_IMAGE_PATH='/media/catalog/product'

# 2018.06.14 by guof.
增加了controllers目录

# 2018.06.15 by guof.
增加对生成lab order的权限限制
ACT_GLO 生成 Lab Order

# 2018.06.20 by guof.
增加了 util ，通用工具类

# 2018.07.21 by guof.
增加了 出库申请单 权限
RN_VIEW 出库申请单
# 2018.07.24 by guof.
增加了 施工单 权限
OCVT_VIEW 施工单

# 2018.07.24 by guof.
增加Lab Order ALL 查看与分配订单权限
OLBO_ALL_VIEW

# 2018.07.31 by guof.
增加 Pg Order 撤销 Review 权限
ACT_CANCEL_REVIEW