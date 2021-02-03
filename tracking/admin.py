# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from tracking.models import *
# Register your models here.
# 归集单
class ai_log_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'object_type',
        'object_entity',
        'doc_number',
        'action',
        'fields',
        'user_name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'object_entity',
        'doc_number',
    ]

    list_filter = (

        'created_at',
        'object_type',
        # 'doc_number',
    )


admin.site.register(ai_log, ai_log_admin)
