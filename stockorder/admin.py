# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import StockOrder, StockInRequest, StockStruct, StockStructLine, InterbranchOrder

class StockOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'stock_order_number',
        'frame',
        'lens_sku',
        'quantity',
        'status',
        'remaining_qty',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'frame',
        'stock_order_number'
    ]

    list_filter = (
        'frame',
        'stock_order_number',
    )


admin.site.register(StockOrder, StockOrderAdmin)


class StockInRequestAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'lab_number',
        'frame',
        'lens_sku',
        'status',
        'quantity',
        'act_quantity',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'frame',
        'lab_number'
    ]

    list_filter = (
        'frame',
        'lab_number',
    )


admin.site.register(StockInRequest, StockInRequestAdmin)



class StockStructAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'frame',
        'lens_sku',
        'warehouse',
        'quantity',
        'location',
        'inbound_type',
    )

    search_fields = [
        'frame',
    ]

    list_filter = (
        'frame',
    )


admin.site.register(StockStruct, StockStructAdmin)


class StockStructLineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'stock_order_number',
        'lab_number',
        'frame',
        'lens_sku',
        'quantity',
        'warehouse',
        'location',
        'inbound_type',
    )

    search_fields = [
        'frame',
        'stock_order_number',
        'lab_number'
    ]

    list_filter = (
        'frame',
        'stock_order_number',
        'lab_number'
    )


admin.site.register(StockStructLine, StockStructLineAdmin)


class InterbranchOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'interbranch_order_number',
        'warehouse_from',
        'location_from',
        'warehouse_to',
        'location_to',
        'frame',
        'lens_sku',
        'sku_attribute',
        'quantity',
        'status',
        'fulfil_date',
        'finish_date',
    )

    search_fields = [
        'frame',
        'interbranch_order_number',
    ]

    list_filter = (
        'frame',
        'interbranch_order_number',
    )


admin.site.register(InterbranchOrder, InterbranchOrderAdmin)