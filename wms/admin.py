# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import product_frame, product_lens, inventory_struct, \
    inventory_initial, inventory_delivery, inventory_receipt, customer_flatrate, \
    warehouse, inventory_struct_warehouse, lens_extend, \
    inventory_initial_lens, inventory_struct_lens, inventory_struct_lens_batch, \
    inventory_delivery_lens, inventory_receipt_lens, channel, inventory_struct_channel, \
    inventory_receipt_channel, inventory_delivery_channel, Lockers


class product_frame_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'parent',
        'product_type',

        'sku',

        'name',
        'base_price',
        'fe',
        'fh',
        'ed',
        'ct',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'product_type',
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(product_frame, product_frame_admin)


class customer_flatrate_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(customer_flatrate, customer_flatrate_admin)


class lens_extend_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'parent',
        'product_type',

        'base_sku',
        'sku',
        'name',
        'index',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'parent',
        'base_sku',
        'sku',
        'name',
    ]

    list_filter = (
        'product_type',
        'index',
        'created_at',
        'updated_at',
        'base_sku',
    )


admin.site.register(lens_extend, lens_extend_admin)


class product_lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'parent',
        'product_type',

        'sku',

        'name',
        'base_price',

        'index',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'parent',
        'sku',
        'name',
    ]

    list_filter = (
        'product_type',
        'index',
        'created_at',
        'updated_at',
    )


admin.site.register(product_lens, product_lens_admin)


class inventory_struct_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'location',
        'quantity',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
        'location',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(inventory_struct, inventory_struct_admin)


class inventory_initial_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'quantity',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'created_at',
    )


admin.site.register(inventory_initial, inventory_initial_admin)


class inventory_delivery_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'quantity',
        'comments',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
        'name'
    )


admin.site.register(inventory_delivery, inventory_delivery_admin)


class inventory_receipt_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'quantity',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(inventory_receipt, inventory_receipt_admin)


class warehouse_admin(admin.ModelAdmin):
    list_display = (
        'code',
        'name',
        'is_enabled'
    )
    search_fields = [
        'code',
        'name'
    ]
    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(warehouse, warehouse_admin)


class inventory_struct_warehouse_admin(admin.ModelAdmin):
    list_display = (
        'sku',
        'name',
        'warehouse_code',
        'warehouse_name',
        'location',
        'quantity',
    )
    search_fields = [
        'sku',
        'warehouse_code',
        'location',
    ]
    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(inventory_struct_warehouse, inventory_struct_warehouse_admin)


# 镜片
class inventory_initial_lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_sku',
        'name',
        'sph',
        'cyl',
        'add',
        'coating',
        'diameter',
        'quantity',

        'created_at',
        'updated_at',
        'batch_number',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'created_at',
        'name',
    )


admin.site.register(inventory_initial_lens, inventory_initial_lens_admin)


class inventory_struct_lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_sku',
        'name',
        'sph',
        'cyl',
        'add',
        'diameter',
        'coating',
        'location',
        'quantity',

        'created_at',
        'updated_at',
        'batch_number',
    )

    search_fields = [
        'sku',
        'name',
        'location',
    ]

    list_filter = (
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(inventory_struct_lens, inventory_struct_lens_admin)


class inventory_struct_lens_batch_admin(admin.ModelAdmin):
    list_display = (
        'base_sku',
        'name',
        'sph',
        'cyl',
        'add',
        'diameter',
        'coating',
        'warehouse_code',
        'warehouse_name',
        'location',
        'quantity',
        'batch_number',
    )
    search_fields = [
        'sku',
        'warehouse_code',
        'location',
        'batch_number',
    ]
    list_filter = (
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(inventory_struct_lens_batch, inventory_struct_lens_batch_admin)


class inventory_delivery_lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_sku',
        'name',
        'quantity',
        # 'comments',
        'warehouse_name',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(inventory_delivery_lens, inventory_delivery_lens_admin)


class inventory_receipt_lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_sku',
        'name',
        'quantity',
        'warehouse_name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(inventory_receipt_lens, inventory_receipt_lens_admin)


# 镜片

class channel_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'code',
        'name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(channel, channel_admin)


class inventory_struct_channel_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'quantity',
        'channel_code',
        'channel_name',
        'type',
        'status',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'name',
        'channel_code',
        'channel_name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
        'name',
    )


admin.site.register(inventory_struct_channel, inventory_struct_channel_admin)


class inventory_receipt_channel_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'quantity',
        'success_status',
        'channel_code',
        'channel_name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'channel_code',
        'channel_name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(inventory_receipt_channel, inventory_receipt_channel_admin)


class inventory_delivery_channel_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'quantity',
        'success_status',
        'channel_code',
        'channel_name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'channel_code',
        'channel_name',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(inventory_delivery_channel, inventory_delivery_channel_admin)


class LockersAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sequence',
        'storage_location',
        'locker_num',
        'quantity',
        'vender',
        'is_enabled',
        'is_send'
    )

    search_fields = [
        'locker_num',
        'storage_location',
    ]

    list_filter = (
        'locker_num',
        'storage_location',
    )


admin.site.register(Lockers, LockersAdmin)