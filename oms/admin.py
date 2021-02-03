# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.utils import timezone

# Register your models here.
from django.contrib import messages
from models.product_models import LabProduct, PgProduct
from models.order_models import *
from models.application_models import OperationLog, ObjectType
from models.dict_models import ProductType
from models.shipping_models import Shipping
from models.ordertracking_models import OrderTracking
from models.generatelog_models import GenerateLog
from models.order_tracking_report_models import OrderTrackingReport
from models.order_tracking_report_cs_models import OrderTrackingReportCS
from models.actions_models import Action
from models.send_comments_models import SendComment
from models.holiday_setting_models import HolidaySetting
from models.shipment_models import Shipment
from models.send_comments_models import SendComment
import logging

admin.site.site_header = "OMS Administration"


class PrescriptionSwap:
    sph = 0.00
    cyl = 0.00
    axis = 0.00


class LabProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'index',
        'is_rx_lab',
        'create_at',
        'update_at',
    )
    search_fields = (
        'sku',
        'name',
    )

    list_filter = (
        'index',
        'is_rx_lab',
        'update_at',
    )


class PgProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'index',
        'is_rx_lab',
        'lab_product',
        'create_at',
        'update_at',
    )
    search_fields = (
        'sku',
        'name',
    )

    list_filter = (
        'index',
        'is_rx_lab',
        'update_at',
    )


admin.site.register(LabProduct, LabProductAdmin)
admin.site.register(PgProduct, PgProductAdmin)


class PgOrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_vip',
        'order_number',
        'product_index',
        'order_date',
        'lab_order_number',
        'comments',

        'frame',
        'lens_sku',
        'lens_name',

        'update_at',
    )
    search_fields = ['order_number',
                     'order_date',
                     'lab_order_number',
                     'frame',
                     'lens_sku',
                     ]

    # actions = ['generate_lab_orders']

    raw_id_fields = (
        'pg_order_entity',
        'lab_order_entity',
    )

    def generate_lab_orders(modelAdmin, request, queryset):
        print 'generate_lab_orders actions hold ....'
        logging.debug(queryset)

        lbos = []
        lbo_ids = []

        for pgo in queryset:
            print pgo

            lbo_ids.append(pgo.id)

        lbo_ids.sort()

        for lbo_id in lbo_ids:
            print lbo_id

        pgos = PgOrderItem.objects.filter(id__in=lbo_ids)

        logging.debug('pg order items list')
        logging.debug(pgos)

        for pgo in pgos:
            # print pgo

            logging.debug(pgo)

            # pgi=PgOrderItem.objects.get(id=pgo.id)
            # 如果瞳高为空，为订单计算瞳高
            if (pgo.lab_seg_height == '' or pgo.lab_seg_height is None) and 'Lined Bifocal' not in pgo.lens_name:
                pgo.lab_seg_height = str(0.5 * float(pgo.lens_height) + 4)
                pgo.assemble_height = 'STD+1.0'
                pgo.comments += '加工瞳高%smm;' % str(0.5 * float(pgo.lens_height) + 4)
                pgo.save()
            rvalue = pgo.generate_lab_orders()

            logging.debug(rvalue)

            if rvalue == 0:
                msg = 'Lab Orders Saved! Pg OrderNumber: %s', pgo.order_number
                messages.add_message(request, messages.SUCCESS, msg)
            else:
                msg = 'Nothing to do!'
                messages.add_message(request, messages.INFO, msg)

    generate_lab_orders.short_description = 'Generate lab orders in pg orders.'


def generate_lab_orders_number(self, order_number, order_date, product_index):
    lab_order_number = ''

    order_number_part = order_number[len(order_number) - 3 - 1:len(order_number) - 1]
    print order_number_part

    return lab_order_number


class LabOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'lab_number',
        'status',
        'type',
        'is_vip',
        'ship_direction',

        'order_date',
        'comments',

        'frame',
        'lens_sku',
        'lens_name',

        'create_at',
        'update_at',
        'production_days_calculate',
        'set_time_calculate',
        'base_entity'

    )

    list_display_links = (
        'id',
        'type',
        'ship_direction',
    )

    search_fields = ['lab_number',
                     'order_date',
                     'frame',
                     'lens_sku',
                     'vendor_order_reference',
                     ]


admin.site.register(PgOrderItem, PgOrderItemAdmin)
admin.site.register(LabOrder, LabOrderAdmin)


class ObjectTypeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'object_type',
        'description',
    )

    list_display_links = (
        'id',
        'type',
        'object_type',
        'description',
    )


admin.site.register(ObjectType, ObjectTypeAdmin)


class OperationLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'object_type',
        'object_entity',
        'doc_number',
        'action',
        'fields',
        'origin_value',
        'new_value',
        'user_name',
        'created_at',
        'updated_at'
    )

    search_fields = [
        'object_type',
        'object_entity',
        'doc_number',
        'action',
        'fields'

    ]
    list_filter = [
        'object_type',
        'action',
        'user_name',
        'created_at',
    ]


admin.site.register(OperationLog, OperationLogAdmin)

admin.site.register(ProductType)


class ShippingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_id',
        'lab_order_id',
        'create_date',
        'first_name',
        'last_name',
        'postcode',
        'street',
        'city',
        'region',
        'country_id',
        'telephone',
        'comment',
    )


admin.site.register(Shipping, ShippingAdmin)


class OrderTrackingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'sku',
        'order_date',
        'username',
        'action_value',
        # 'print_date',
        # 'frame_outbound',
        # 'add_hardened',
        # 'coating',
        # 'tint',
        # 'lens_receive',
        # 'assembling',
        # 'initial_inspection',
        # 'shaping',
        # 'purging',
        # 'final_inspection',
        # 'order_match',
        # 'package',
        # 'shipping',
        # 'estimated_time',
        # 'final_time',
        'remark',
    )

    search_fields = ['order_number',
                     'sku',
                     ]

    raw_id_fields = (
    #    'lab_order_entity',
    #    'user_entity',
    )

admin.site.register(OrderTracking, OrderTrackingAdmin)


class GenerateLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'last_entity',
        'current_entity',
        'create_at',
        'update_at',
    )


admin.site.register(GenerateLog, GenerateLogAdmin)


class OrderTrackingReportAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'lab_order_number',
        'order_date',
        'print_date',
        'frame_outbound',
        'add_hardened',
        'coating',
        'tint',
        'lens_receive',
        'assembling',
        'initial_inspection',
        'shaping',
        'purging',
        'final_inspection',
        'order_match',
        'package',
        'shipping',
    )


admin.site.register(OrderTrackingReport, OrderTrackingReportAdmin)


class OrderTrackingReportCSAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'pgorder_number',
        'shipping_method',
        'order_number',
        'sku',
        'order_date',
        'cs_status',
        'estimated_time',
        'final_time',
        'carriers',
        'shipping_number',
        'remark',
    )


admin.site.register(OrderTrackingReportCS, OrderTrackingReportCSAdmin)


class OrderActivityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'object_type',
        'object_entity',
        'order_number',
        'action',
        'user_entity',
        'user_name',
        'comments',
        'is_async',
    )


admin.site.register(OrderActivity, OrderActivityAdmin)


class ActionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'key',
        'value',
        'object_type',
        'description',
        'help',
        'sequence',
    )


admin.site.register(Action, ActionAdmin)


class PgOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_vip',
        'order_number',
        'order_date',

        'comments',

        'subtotal',
        'grand_total',
        'total_paid',
        'shipping_and_handling',
        'base_discount_amount_order',
        'total_qty_ordered',

        'update_at',
    )

    search_fields = ['order_number',
                     'order_date',
                     ]


admin.site.register(PgOrder, PgOrderAdmin)


class HolidaySettingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'country_id',
        'holiday_date',
    )


admin.site.register(HolidaySetting, HolidaySettingAdmin)


class LabOrder_QualityControlAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_entity',
        'comments',
    )


admin.site.register(LabOrder_QualityControl, LabOrder_QualityControlAdmin)


class SendCommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'key',
        'value',
    )


admin.site.register(SendComment, SendCommentAdmin)


class ShipmentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'carrierNumber',
        'carrier',
        'remark'
    )


admin.site.register(Shipment, ShipmentAdmin)


class laborder_request_notes_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',
        'count',

        'created_at'
    )

    list_filter = (
        'created_at',
    )


admin.site.register(laborder_request_notes, laborder_request_notes_admin)


class laborder_request_notes_line_admin(admin.ModelAdmin):
    list_display = (
        'id',

        'index',
        'frame',
        'lab_number',
        'quantity',
        'lens_type',
        'laborder_id',

        'created_at',
    )

    list_filter = (
        'lrn__created_at',
    )


admin.site.register(laborder_request_notes_line, laborder_request_notes_line_admin)


class factory_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'factory_id',
        'factory_name'
    )


admin.site.register(factory, factory_admin)


class laborder_purchase_order_line_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',
        'lens_type',
        'purchase_type',
        'is_set_hours_of_purchase',
        'vendor_order_reference'
    )

    search_fields = [
        'vendor_order_reference',
        'lab_number',
    ]


admin.site.register(laborder_purchase_order_line, laborder_purchase_order_line_admin)


class hold_cancel_request_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'created_at',
        'lab_number',
        'user_name',
        'reply_username',
        'order_status_now',
        'order_status_future',
        'reason',
        'reply'
    )
    search_fields = [
        'lab_number'
    ]
    list_filter = (
        'created_at',
        'order_status_now',
        'order_status_future',
        'user_name',
        'reply_username',
    )

admin.site.register(hold_cancel_request, hold_cancel_request_admin)

class CustomerAccountLog_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'is_pwd',
        'customer_email',
        'old_customer_email',
        'user_entity',
        'created_at',
        'updated_at'
    )
    search_fields = [
        'customer_email',
        'old_customer_email',
    ]
    list_filter = (
        'user_entity',
    )
admin.site.register(CustomerAccountLog, CustomerAccountLog_admin)



class RemakeOrder_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'item_id',
        'remake_order',
        'user_name',
        'created_at',
        'updated_at'
    )
    search_fields = [
        'order_number',
        'remake_order',
    ]
    list_filter = (
        'user_name',
    )
admin.site.register(RemakeOrder, RemakeOrder_admin)


class BlueGlassesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'frame',
        'created_at',
        'updated_at'
    )
    search_fields = [
        'frame',
    ]
    list_filter = (
        'frame',
    )
admin.site.register(BlueGlasses, BlueGlassesAdmin)