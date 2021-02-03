# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import comment


class comment_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'biz_type',
        'biz_id',

        'comments',

        'status',
        'user_name',
        'assign_name',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'biz_type',
        'biz_id',
    ]

    list_filter = (
        'biz_type',
        'status',
        'user_name',
        'assign_name',
    )

admin.site.register(comment, comment_admin)
