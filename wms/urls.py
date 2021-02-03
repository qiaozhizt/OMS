from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='wms_index'),

    url(r'^delivery/frame/$', views.redirect_delivery_frame, name='wms_delivery_frame'),
    url(r'^delivery/frame_post/$', views.ajax_delivery_frame, name='wms_delivery_frame_post'),

    url(r'^delivery/frame_lens/$', views.redirect_delivery_frame_lens, name='wms_delivery_frame_lens'),
    url(r'^delivery/frame_lens_post/$', views.ajax_delivery_frame_lens, name='wms_delivery_frame_lens_post'),
    # url(r'^all/$', views.redirect_comments, name='comments'),

    url(r'^inventory_struct/$', views.redirect_inventory_struct, name='wms_inventory_struct'),
    url(r'^inventory_struct_warehouse/$', views.redirect_inventory_struct_warehouse,
        name='wms_inventory_struct_warehouse'),

    url(r'^inventory_struct_warehouse_csv/$', views.redirect_inventory_struct_warehouse_csv,
        name='wms_inventory_struct_warehouse_csv'),


    url(r'^inventory_struct_warehouse_location/$', views.redirect_inventory_struct_warehouse_location,
        name='wms_inventory_struct_warehouse_location'),

    url(r'^inventory_receipt/$', views.redirect_inventory_receipt, name='wms_inventory_receipt'),
    url(r'^inventory_receipt_submit/$', views.redirect_inventory_receipt_submit, name='inventory_receipt_submit'),
    url(r'^inventory_delivery/$', views.redirect_inventory_delivery, name='wms_inventory_delivery'),
    url(r'^inventory_delivery_submit/$', views.redirect_inventory_delivery_submit,
        name='wms_inventory_delivery_submit'),

    url(r'^update_estimate_replenishment_date/$', views.update_estimate_replenishment_date,
        name='update_replenishment_date'),

    url(r'^edit_retired$', views.edit_retired, name='edit_retired'),
    url(r'^edit_lock_quantity', views.edit_lock_quantity, name='edit_lock_quantity'),
    url(r'^edit_stock', views.edit_stock, name='edit_stock'),

    url(r'^inventory_receipt_lens/$', views.redirect_inventory_receipt_lens, name='wms_inventory_receipt_lens'),
    url(r'^inventory_delivery_lens/$', views.redirect_inventory_delivery_lens, name='wms_inventory_delivery_lens'),
    url(r'^inventory_receipt_lens_submit/$', views.redirect_inventory_receipt_lens_submit,
        name='inventory_receipt_lens_submit'),
    url(r'^inventory_delivery_lens_submit/$', views.redirect_inventory_delivery_lens_submit,
        name='wms_inventory_delivery_lens_submit'),
    url(r'^inventory_struct_lens/$', views.redirect_inventory_struct_lens, name='wms_inventory_struct_lens'),
    url(r'^inventory_struct_lens_detail/$', views.redirect_inventory_struct_lens_detail,
        name='wms_inventory_struct_lens_detail'),
    url(r'^inventory_struct_lens_calibration_upload_excel/$', views.inventory_struct_lens_calibration_upload_excel,
        name='wms_inventory_struct_lens_calibration_upload_excel'),
    url(r'^inventory_struct_lens_calibration/$', views.inventory_struct_lens_calibration,
        name='wms_inventory_struct_lens_calibration'),
    url(r'^inventory_struct_lens_calibration_do/$', views.inventory_struct_lens_calibration_do,
        name='wms_inventory_struct_lens_calibration_do'),

    url(r'^inventory_frame_receipt_report/$', views.inventory_frame_receipt_report,
        name='wms_inventory_frame_receipt_report'),
    url(r'^inventory_frame_receipt_report_print/$', views.inventory_frame_receipt_report_print,
        name='wms_inventory_frame_receipt_report_print'),
    url(r'^inventory_frame_receipt_report_export_excel/$', views.inventory_frame_receipt_report_export_excel,
        name='wms_inventory_frame_receipt_report_export_excel'),

    url(r'^inventory_frame_delivery_report/$', views.inventory_frame_delivery_report,
        name='wms_inventory_frame_delivery_report'),
    url(r'^inventory_frame_delivery_report_print/$', views.inventory_frame_delivery_report_print,
        name='wms_inventory_frame_delivery_report_print'),
    url(r'^inventory_frame_delivery_report_export_excel/$', views.inventory_frame_delivery_report_export_excel,
        name='wms_inventory_frame_delivery_report_export_excel'),

    url(r'^inventory_lens_receipt_report/$', views.inventory_lens_receipt_report,
        name='wms_inventory_lens_receipt_report'),
    url(r'^inventory_lens_receipt_report_print/$', views.inventory_lens_receipt_report_print,
        name='wms_inventory_lens_receipt_report_print'),
    url(r'^inventory_lens_receipt_report_export_excel/$', views.inventory_lens_receipt_report_export_excel,
        name='wms_inventory_lens_receipt_report_export_excel'),

    url(r'^inventory_lens_delivery_report/$', views.inventory_lens_delivery_report,
        name='wms_inventory_lens_delivery_report'),
    url(r'^inventory_lens_delivery_report_print/$', views.inventory_lens_delivery_report_print,
        name='wms_inventory_lens_delivery_report_print'),
    url(r'^inventory_lens_delivery_report_export_excel/$', views.inventory_lens_delivery_report_export_excel,
        name='wms_inventory_lens_delivery_report_export_excel'),

    url(r'^product_management/$', views.redirect_product_management,
        name='wms_product_management'),
    url(r'^inventory_dis_quantity/$', views.inventory_dis_quantity,
        name='wms_inventory_dis_quantity'),
    url(r'^distribution_withdrawal_list/$', views.redirect_distribution_withdrawal_list,
        name='wms_distribution_withdrawal_list'),
    url(r'^inventory_again_dis_quantity/$', views.redirect_inventory_again_dis_quantity,
        name='wms_inventory_again_dis_quantity'),
    url(r'^inventory_sync_web_data/$', views.redirect_inventory_sync_web_data,
        name='wms_inventory_sync_web_data'),
    url(r'^inventory_sync_reserve_quantity/$', views.redirect_inventory_sync_reserve_quantity,
        name='wms_inventory_sync_reserve_quantity'),
    url(r'^inventory_sync_difference/$', views.redirect_inventory_sync_difference,
        name='wms_inventory_sync_difference'),
    url(r'^redirect_inventory_sync_reason/$', views.redirect_inventory_sync_reason,
        name='redirect_inventory_sync_reason'),
    url(r'^wms_lockers_list/$', views.lockers_list, name='wms_lockers_list'),
    url(r'^init_lockers/$', views.init_lockers, name='init_lockers'),
    url(r'^remove_locker/$', views.remove_locker, name='remove_locker'),
    url(r'^locker_vender_set/$', views.locker_vender_set, name='locker_vender_set'),
    url(r'^lockers_log/$', views.lockers_log, name='lockers_log'),
    url(r'^wms_production_sku_history/$', views.wms_production_sku_history, name='wms_production_sku_history'),
    url(r'^get_product_lens_sph/$', views.get_product_lens_sph, name='get_product_lens_sph'),
    url(r'^get_product_lens_cyl/$', views.get_product_lens_cyl, name='get_product_lens_cyl'),
    url(r'^product_management_excel/$', views.redirect_product_management_excel,
        name='wms_product_management_excel'),
    url(r'^update_cargo_location/$', views.update_cargo_location, name='update_cargo_location'),
    url(r'^wms_add_edit_product_frame/$', views.wms_add_edit_product_frame, name='wms_add_edit_product_frame'),
    url(r'^wms_edit_product_frame/$', views.wms_edit_product_frame, name='wms_edit_product_frame'),
    url(r'^wms_save_product_frame/$', views.wms_save_product_frame, name='wms_save_product_frame'),
    url(r'^wms_add_product_frame/$', views.wms_add_product_frame, name='wms_add_product_frame'),
    url(r'^wms_add_edit_warehouse/$', views.wms_add_edit_warehouse, name='wms_add_edit_warehouse'),
    url(r'^wms_edit_warehouse/$', views.wms_edit_warehouse, name='wms_edit_warehouse'),
    url(r'^wms_save_warehouse/$', views.wms_save_warehouse, name='wms_save_warehouse'),
    url(r'^wms_add_warehouse/$', views.wms_add_warehouse, name='wms_add_warehouse'),
    url(r'^edit_no_sale_quantity', views.edit_no_sale_quantity, name='edit_no_sale_quantity'),
    # VCA download
    url(r'^download', views.file_download, name='file_download'),

]
# url(r'^mgmt/$', views.index, name='mgmt'),
