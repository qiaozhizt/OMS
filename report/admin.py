# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from report.models import *

admin.site.register(customize_report, customize_report_admin)


# chen
class lens_report_line_admin(admin.ModelAdmin):
    list_display = (
        'type',
        'lr',
        'period',
        'good',
        'general',
        'bad',
        'report_day',
        'total',
    )

    search_fields = [
        'type',
        'range',
    ]

    list_filter = (
        'type',

    )


admin.site.register(lens_report_line, lens_report_line_admin)


class ReportConfigAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'subscribe',
        'comments',
    )

    search_fields = [
        'name',
    ]

    list_filter = (
        'name',

    )


admin.site.register(ReportConfig, ReportConfigAdmin)


class ReportInfoAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'year',
        'month',
        'day',
        'mold',
        'comments',
        'is_send'
    )

    search_fields = [
        'name',
    ]

    list_filter = (
        'name',

    )


admin.site.register(ReportInfo, ReportInfoAdmin)


class ReportInfoLineAdmin(admin.ModelAdmin):
    list_display = (
        'base_entity',
        'item',
        'quantity',
    )

    search_fields = [
        'item',
    ]

    list_filter = (
        'item',

    )


admin.site.register(ReportInfoLine, ReportInfoLineAdmin)
