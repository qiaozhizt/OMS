# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import *

# Register your models here.

class AssemblerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_code',
        'user_name',
        'department',
        'is_enabled',
        'created_at',
    )
    search_fields = (
        'user_code',
        'user_name',
        'department',
    )

    list_filter = (
        'department',
        'is_enabled',
        'user_name',
    )

admin.site.register(Assembler, AssemblerAdmin)
