# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import AccsOrder, AccsOrderRequestNotes, AccsOrderRequestNotesLine, AccsOrderDeliveryLine, AccsOrderTracking


class AccsOrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'accs_order_number',
        'sku',
        'name',
        'quantity',
        'warehouse',
        'status',
        'order_number',
        'is_rx_have',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'sku',
        'accs_order_number',
        'order_number',
    ]

    list_filter = (
        'sku',
        'status',
    )


admin.site.register(AccsOrder, AccsOrderAdmin)


class AccsOrderRequestNotesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'accs_order_number',
        'warehouse',
        'accsorder_id',
    )

    search_fields = [
        'accsorder_id',
        'accs_order_number',
    ]

    list_filter = (
        'accs_order_number',
    )


admin.site.register(AccsOrderRequestNotes, AccsOrderRequestNotesAdmin)


class AccsOrderRequestNotesLineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'accs_order_number',
        'base_entity',
        'accsorder_id',
        'sku',
        'quantity',
        'warehouse',
    )

    search_fields = [
        'sku',
        'accs_order_number',
    ]

    list_filter = (
        'accs_order_number',
    )


admin.site.register(AccsOrderRequestNotesLine, AccsOrderRequestNotesAdmin)


class AccsOrderDeliveryLineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'accs_order_number',
        'base_entity',
        'sku',
        'quantity',
        'warehouse',
    )

    search_fields = [
        'sku',
        'accs_order_number',
    ]

    list_filter = (
        'accs_order_number',
    )


admin.site.register(AccsOrderDeliveryLine, AccsOrderDeliveryLineAdmin)


class AccsOrderTrackingAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'action',
        'user_id',
        'user_name',
        'comments',
    )

    search_fields = [
        'order_number',
    ]

    list_filter = (
        'order_number',
    )


admin.site.register(AccsOrderTracking, AccsOrderTrackingAdmin)