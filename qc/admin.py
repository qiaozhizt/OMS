# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

# Register your models here.
from .models import *


class lens_registration_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'laborder_id',
        'lab_number',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(lens_registration, lens_registration_admin)


class preliminary_checking_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',

        'is_qualified',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'laborder_id',
        'lab_number',
    ]

    list_filter = (
        'is_qualified',
        'created_at',
        'updated_at',
    )


admin.site.register(preliminary_checking, preliminary_checking_admin)


class glasses_final_inspection_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',

        'is_qualified',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'laborder_id',
        'lab_number',
    ]

    list_filter = (
        'is_qualified',
        'created_at',
        'updated_at',
    )


admin.site.register(glasses_final_inspection, glasses_final_inspection_admin)


class glasses_final_inspection_log_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',

        'reason_code',
        'reason',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'laborder_id',
        'lab_number',
        'reason_code',
        'reason'
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(glasses_final_inspection_log, glasses_final_inspection_log_admin)


class glasses_final_inspection_technique_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'laborder_id',
        'lab_number',

        'pd',
        'is_singgle_pd',
        'od_pd',
        'os_pd',
        'blue_blocker',
        'polarized',
        'is_qualified',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'laborder_id',
        'lab_number',
    ]

    list_filter = (
        'is_qualified',
        'created_at',
        'updated_at',
    )


admin.site.register(glasses_final_inspection_technique, glasses_final_inspection_technique_admin)


class prescripiton_actual_admin(admin.ModelAdmin):
    list_display = (
        'id',

        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(prescripiton_actual, prescripiton_actual_admin)


class glasses_final_appearance_visual_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'lab_number',
        'is_frame',
        'is_parts',
        'is_lens',
        'is_assembling',
        'is_plastic',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'lab_number',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(glasses_final_appearance_visual, glasses_final_appearance_visual_admin)


class glasses_unqualified_items_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'item_id',
        'item_name',
        'appearance_id',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'item_id',
        'item_name',
        'appearance_id',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(glasses_unqualified_items, glasses_unqualified_items_admin)

class glasses_unqualified_items_config_admin(admin.ModelAdmin):
    list_display = (
        'id',
        'item_name',
        'item_type',
        'created_at',
        'updated_at',
    )

    search_fields = [
        'id',
        'item_name',
        'item_type',
    ]

    list_filter = (
        'created_at',
        'updated_at',
    )


admin.site.register(glasses_unqualified_items_config, glasses_unqualified_items_config_admin)


class LensReasonAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reason_code',
        'reason_name',
        'is_enabled',
        'created_at',
    )

    search_fields = [
        'id',
        'reason_code',
        'reason_name',
    ]

    list_filter = (
        'reason_code',
    )


admin.site.register(LensReason, LensReasonAdmin)

class FrameReasonAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'reason_code',
        'reason_name',
        'is_enabled',
        'created_at',
    )

    search_fields = [
        'id',
        'reason_code',
        'reason_name',
    ]

    list_filter = (
        'reason_code',
    )


admin.site.register(FrameReason, FrameReasonAdmin)
