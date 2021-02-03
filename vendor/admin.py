# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from models import *


class corp_apps_info_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'vendor_code',
        'vendor_name',
        'corp_id',
        'app_key',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'vendor_code',
        'vendor_name',
        'corp_id',
        'app_key',
    )

    list_filter = (
        'vendor_code',
        'created_at',
        'updated_at',
    )


class lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'lens_type',
        'base_sku',
        'sku',
        'name',
        'index',
        'vd_lens_sku',
        'vendor_code',
        'priority',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'base_sku',
        'sku',
        'name',
        'vd_lens_sku',
    )

    list_filter = (
        'lens_type',
        'vendor_code',
        'index',
        'updated_at',
        # 'base_sku',
    )


class lens_order_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'lab_number',
        'status',
        'lens_sku',
        'lens_name',
        'sph',
        'cyl',
        'axis',
        'pd',
        'rl_identification',
        'vendor',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'order_number',
        'lab_number',
        'lens_sku',
        'vendor',
    )

    list_filter = (
        'vendor',
        'updated_at',
    )


class distribute_log_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'lab_number',
        'lens_sku',
        'lens_name',
        'vendor',
        'user_name',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'order_number',
        'lab_number',
        'lens_sku',
        'vendor',
    )

    list_filter = (
        'user_name',
        'status',
        'vendor',
        'updated_at',
    )

class distribute_configuration_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'type',
        'key',
        'value',
        'user_name',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'key',
        'value',
    )

    list_filter = (
        'user_name',
        'created_at',
        'updated_at',
    )

class wx_product_contrast_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'act_lens_sku',
        'channel',
        'lens_type',
        'index',
        'wx_name',
        'name',

    )

    search_fields = (
        'code',
        'act_lens_sku',
    )

    list_filter = (
        'index',
        'act_lens_sku',
    )

class wc_lens_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'code',
        'lab_lens_sku',
        'index',
        'material_sku',
        'product_sku',
        'product_name',

    )

    search_fields = (
        'code',
        'lab_lens_sku',
    )

    list_filter = (
        'index',
        'lab_lens_sku',
        'material_sku',
        'product_sku',
    )

class wx_product_relationship_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'name',
        'wx_name',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'sku',
        'name',
        'wx_sku',
        'wx_name',
    )

    list_filter = (
        'created_at',
        'updated_at',
    )

admin.site.register(corp_apps_info, corp_apps_info_admin)
admin.site.register(lens, lens_admin)
admin.site.register(lens_order, lens_order_admin)
admin.site.register(distribute_log, distribute_log_admin)
admin.site.register(distribute_configuration, distribute_configuration_admin)
admin.site.register(wx_product_contrast, wx_product_contrast_admin)
admin.site.register(wc_lens, wc_lens_admin)
admin.site.register(wx_product_relationship,wx_product_relationship_admin)


class WxMetaProductRelationshipAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sku',
        'productName',
        'productId',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'sku',
        'productName',
        'productId',
    )

    list_filter = (
        'created_at',
        'updated_at',
    )

admin.site.register(WxMetaProductRelationship, WxMetaProductRelationshipAdmin)