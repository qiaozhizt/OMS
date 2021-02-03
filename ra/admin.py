# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import *

class RaEntityAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'state',
        'status',
        'ra_type',

        'order_number',
        'ticket_id_part',

        'quantity',
        'amount',
        'label_id',

        'user_name',
        'created_at',
    )

    search_fields = [
        'order_number',
        'ticket_id_part',
    ]

    list_filter = (
        'created_at',
        'user_name',

        'state',
        'status',
        'ra_type',
    )

admin.site.register(RaEntity,RaEntityAdmin)


class RaItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_entity',
        'frame',

        'quantity',
        'created_at',
    )

    search_fields = [
        'base_entity',
        'frame',
    ]

    list_filter = (
        'created_at',
    )

admin.site.register(RaItem,RaItemAdmin)


class RaLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'base_entity',
        'base_type',
        'action',
        'action_value',

        'comments',
        'user_name',
        'created_at',
    )

    search_fields = [
        'base_entity',
        'comments',
    ]

    list_filter = (
        'created_at',
        'user_name',

        'action',
    )

admin.site.register(RaLog,RaLogAdmin)
