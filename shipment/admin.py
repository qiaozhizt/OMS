# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import pre_delivery, pre_delivery_line, collection_glasses, received_glasses, glasses_box, glasses_box_item


# Register your models here.
class pre_delivery_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'status',
        'shipping_method',

        'e_count',
        'w_count',
        'express_count',
        'other_count',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'status',
        'id',
    ]

    list_filter = (
        'status',
        'shipping_method',
        'created_at',
    )


admin.site.register(pre_delivery, pre_delivery_admin)


# Register your models here.
class pre_delivery_line_admin(admin.ModelAdmin):
    list_display = (
        'id',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
    ]

    list_filter = (

        'created_at',
    )


admin.site.register(pre_delivery_line, pre_delivery_line_admin)


# 归集单
class collection_glasses_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'collection_number',
        'order_number',
        'lab_number',
        'status',
        'send_from',
        'send_to',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'collection_number',
        'order_number',
        'lab_number',
    ]

    list_filter = (

        'created_at',
        'collection_number',
    )


admin.site.register(collection_glasses, collection_glasses_admin)


class glasses_box_admin(admin.ModelAdmin):
    list_display = (
        'type',
        'tracking_number',
        'carrier',
        'region',
        'box_id',
    )

    search_fields = [
        'type',
        'cur_bag_id',
        'box_id',
        'box_id_1',
        'tracking_number',
        'region',
    ]

    list_filter = (
        'type',
    )


admin.site.register(glasses_box, glasses_box_admin)


class glasses_box_item_admin(admin.ModelAdmin):
    list_display = (
        'type',
        'order_number',
        'lab_number',
        'lab_frame',
        'name',
        'street1',
        'street2',
        'city',
        'state',
        # 'instruction',
        # 'comments_ship',
        'is_issue_addr',
        'is_verified_addr',
    )

    search_fields = [
        'box_id',
        'order_number',
    ]

    list_filter = (
        'type',
        # 'box_id',
        # 'bag_id',
        # 'order_number',
        # 'lab_number',
    )


admin.site.register(glasses_box_item, glasses_box_item_admin)
