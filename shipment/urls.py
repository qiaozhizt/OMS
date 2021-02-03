from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='api_index'),
    url(r'^address/$', views.redirect_address,
        name='shipment_address'),
    url(r'^address_verify/$', views.redirect_address_verify,
        name='shipment_address_verify'),
    url(r'^collection_glasses/$', views.redirect_collection_glasses,
        name='collection_glasses'),
    url(r'^shipments_received_glasses/$', views.redirect_shipments_received_glasses,
        name='shipments_received_glasses'),

    url(r'^pre_delivery/$', views.redirect_pre_delivery,
        name='pre_delivery'),

    url(r'^pre_delivery_shipped/$', views.redirect_pre_delivery_shipped,
        name='pre_delivery_shipped'),

    url(r'^delivery/$', views.redirect_delivery,
        name='delivery'),

    url(r'^delivery/detail/$', views.redirect_delivery_detail,
        name='delivery_detail'),

    url(r'^pre_delivery_update_status/$', views.redirect_pre_delivery_update_status,
        name='pre_delivery_update_status'),

    url(r'^pre_delivery_update_status_final_inspection_line/$',
        views.redirect_pre_delivery_update_status_final_inspection_line,
        name='pre_delivery_update_status_final_inspection_line'),

    url(r'^pre_delivery_print_addr/$',
        views.redirect_pre_delivery_print_addr,
        name='pre_delivery_print_addr'),

    url(r'^pre_delivery_convert/$',
        views.redirect_pre_delivery_convert,
        name='pre_delivery_convert'),

    url(r'^glasses_boxing/$', views.redirect_glasses_boxing,
        name='glasses_boxing'),

    url(r'^glasses_boxing_scan/$', views.redirect_glasses_boxing_scan,
        name='glasses_boxing_scan'),

    url(r'^glasses_boxing_create_bag/$', views.redirect_glasses_boxing_create_bag,
        name='glasses_boxing_create_bag'),

    url(r'^pre_delivery_set_shippingmethod/$', views.redirect_pre_delivery_set_shippingmethod,
        name='pre_delivery_set_shippingmethod'),

    url(r'^glasses_boxing_post_box/$', views.redirect_glasses_boxing_post_box,
        name='glasses_boxing_post_box'),

    url(r'^calculate_combined_shipment/$', views.redirect_calculate_combined_shipment,
        name='shipment_calculate_combined_shipment'),
    url(r'^laborder_status_change/$', views.redirect_laborder_status_change,
        name='laborder_status_change'),
    url(r'^open_close_box/$', views.redirect_open_close_box,
        name='shipment_open_close_box'),

    url(r'^shipping/orders/$', views.redirect_shipping_orders, name='shipping_orders'),
    url(r'^shipping/orders/csv/$', views.redirect_shipping_orders_csv, name='shipping_orders_csv'),
    url(r'^upload_excel$', views.redirect_upload_excel, name='shipping_upload_excel'),

    url(r'^delivered/orders/$', views.redirect_delivered_orders, name='delivered_orders'),
    url(r'^delivered/orders/csv/$', views.redirect_delivered_orders_csv, name='delivered_orders_csv'),

]
