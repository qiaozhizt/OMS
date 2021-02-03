# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import documents_base, statement_lab_order_lens_daily,statement_lab_order_lens_daily_line


#chen
class statement_lab_order_lens_daily_admin(admin.ModelAdmin):
    list_display = (
        'type',
        'workshop',
        'vendor',
        'order_number',
    )

    search_fields = [
        'type',
        'workshop',
        'order_number',
    ]

    list_filter = (
        'type',
        'workshop',
        'vendor',
        'order_number',
    )


admin.site.register(statement_lab_order_lens_daily, statement_lab_order_lens_daily_admin)


#chen
class statement_lab_order_lens_daily_line_admin(admin.ModelAdmin):
    list_display = (
        'type',
        'parent',
        'pg_order_entity_id',
        'order_number',
        'lab_order_entity_id',
        'lab_number',
        'order_date',
        'frame',
        'name',
        'quantity',
        # 'lens_sku',
        # 'coating_sku',
        'coating_name',
        # 'tint_sku',
        'tint_name',
        # 'pal_design_sku',
        'pal_design_name',
        'workshop',
    )

    search_fields = [
        'order_number',
        'lens_sku', #sku标识是惟一的
    ]

    list_filter = (
        'type',
        'workshop',
        'order_number',
        'name',
        'quantity',
        'lens_sku',
        'coating_sku',
        'tint_sku',
        'pal_design_sku',
        'workshop',
    )


admin.site.register(statement_lab_order_lens_daily_line, statement_lab_order_lens_daily_line_admin)


