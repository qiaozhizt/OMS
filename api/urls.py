from django.conf.urls import url
from . import views
from . import control
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='api_index'),

    url(r'^orders/status/renew/$', views.OrdersStatusRenew.as_view(),
        name='orders_status_renew'),

    url(r'^laborders/(.*)/$', views.redirect_laborders_query,
        name='api_laborder_query'),

    url(r'^pg_orders/(.*)/$', views.redirect_pg_orders_query,
        name='api_pg_orders_query'),

    url(r'^pgorder_address_verified/$', views.redirect_pgorder_address_verified,
        name='api_pgorder_address_verified'),
    url(r'^pgorder_address_verified_google/$', views.redirect_pgorder_address_verified_google,
        name='api_pgorder_address_verified_google'),

    url(r'^address_verified/$', views.address_verified_api,
        name='api_address_verified'),

    url(r'^qc_glasses_final_inspection/$', views.redirect_qc_glasses_final_inspection,
        name='qc_glasses_final_inspection'),

    url(r'^get_lab_number/(.*)/$', views.redirect_get_lab_number,
        name='get_lab_number'),

    url(r'^get_lab_numbers/$', views.redirect_get_lab_numbers,
        name='get_lab_numbers'),

    url(r'^change_status/$', views.redirect_change_status,
        name='change_status'),

    url(r'^redirect_quality_inspection_query/(.*)/$', views.redirect_quality_inspection_query,
        name='api_redirect_quality_inspection_query'),

    url(r'^set_is_has_imgs/$', views.set_is_has_imgs, name='set_is_has_imgs'),

    url(r'^pg_order_item_is_has_imgs/$', views.PgOrderItemIsHasImgs.as_view(), name='pg_order_item_is_has_imgs'),

    url(r'^LaborderAccessories/$', views.LaborderAccessories.as_view(), name='LaborderAccessories'),
    url(r'^InventoryReceiptLens/$', views.InventoryReceiptLens.as_view(), name='InventoryReceiptLens'),
    url(r'^InventoryStructs/$', views.LensInventoryStructs.as_view(), name='InventoryStructs'),

    url(r'^InventoryStructsStatus/$', views.InventoryStructsStatus.as_view(), name='InventoryStructsStatus'),
    url(r'^write_back_pgorder_invoice/$', views.PgOrder_Invoice.as_view(), name='write_back_pgorder_invoice'),
    url(r'^get_pg_orders/(.*)/$', views.GetPgOrders.as_view(), name='pg_orders'),
    url(r'^ShipmentHistorys/$', views.ShipmentHistorys.as_view(), name='ShipmentHistorys'),

    url(r'^get_delivery_info/$', views.GetDeliveryInfo.as_view(), name='get_delivery_info'),
    url(r'^SetLabOrderStatusDelivered/$', views.SetLabOrderStatusDelivered.as_view(), name='SetLabOrderStatusDelivered'),
    url(r'^dingding_chat/$', views.RedirectDingdingChat, name='dingding_chat'),
    url(r'^pg_order/hold_request/$', views.pg_order_hold_request, name='pg_order_hold_request'),
    url(r'^get_order_delivered_list/$', views.GetOrderDeliveredList.as_view(), name='get_order_delivered_list'),
    url(r'^pg_order/cancle_warranty_request/$', views.pg_cancle_warranty_request, name='pg_cancle_warranty_request'),

    url(r'^reorder/rules_3001/$', views.redirect_api_reorder_rules_3001, name='api_reorder_rules_3001'),
    url(r'^reorder/rules_3002/$', views.redirect_api_reorder_rules_3002, name='api_reorder_rules_3002'),
    url(r'^reorder/rules_3009/$', views.redirect_api_reorder_rules_3009, name='api_reorder_rules_3003'),
    url(r'^reorder/add_to_cart/$', views.redirect_api_add_to_cart, name='api_add_to_cart'),
    url(r'^reorder/del_cart/$', views.redirect_api_del_cart, name='api_del_cart'),
    url(r'^reorder/gennerate_web_order/$', views.redirect_api_web_order, name='api_web_order'),

    url(r'^reorder/verification_prescription/$', views.redirect_api_verification_prescription, name='api_reorder_verification_prescription'),
    url(r'^upload_product_file/$', views.UploadFile.as_view(), name='api_upload_product_file'),
    url(r'^qc_glasses_first_inspection/$', views.QcGlassesFirstInspection.as_view(), name='api_qc_glasses_first_inspection'),
    url(r'^account/login$', control.api_login, name='api_login'),
    url(r'^set_glasses_weight/$', views.SetGlassesWeight.as_view(), name='api_set_glasses_weight'),
    url(r'^get_frame_vca/$', views.GetFrameVca.as_view(), name='api_get_frame_vca'),
    url(r'^get_laborder_data/$', views.GetLaborderData.as_view(), name='api_get_laborder_data'),
    url(r'^change_laborder_is_push/$', views.ChangeLabOrderIsPush.as_view(), name='api_change_laborder_is_push'),
    url(r'^get_laborders/$', views.GetLaborders.as_view(),name='api_get_laborders'),
]

