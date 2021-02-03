# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from models import *


class job_tracking_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'entity_id',
        'lab_number',
        'status',
        'frame',
        'lens_sku',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'order_number',
        'entity_id',
        'lab_number',
    )

    list_filter = (
        'created_at',
    )


admin.site.register(job_tracking, job_tracking_admin)


class job_archived_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
        'entity_id',
        'lab_number',
        'status',
        'frame',
        'lens_sku',
        'created_at',
        'updated_at',
    )
    search_fields = (
        'order_number',
        'entity_id',
        'lab_number',
    )

    list_filter = (
        'created_at',
    )


admin.site.register(job_archived, job_archived_admin)


class job_log_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'last_entity_id',
        'created_at',
        'updated_at',
    )

    search_fields = (
        'last_entity_id',
    )

    list_filter = (
        'created_at',
    )


admin.site.register(job_log, job_log_admin)
