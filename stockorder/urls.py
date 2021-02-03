from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^stock_order_new/$', views.redirect_stock_order_new, name='stock_order_new'),
    url(r'^stock_order_new_data/$', views.redirect_stock_order_new_data, name='stock_order_new_data'),
    url(r'^stock_order_save/$', views.redirect_stock_order_save, name='stock_order_save'),
    url(r'^stock_order_list/$', views.redirect_stock_order_list, name='stock_order_list'),
    url(r'^change_stock_order_status/$', views.redirect_change_stock_order_status, name='change_stock_order_status'),
    url(r'^create_stock_in_request_list/$', views.redirect_create_stock_in_request_list, name='create_stock_in_request_list'),
    url(r'^get_stko_laborder_data/$', views.redirect_get_stko_laborder_data, name='get_stko_laborder_data'),
    url(r'^create_stock_in_request/$', views.redirect_create_stock_in_request, name='create_stock_in_request'),
    url(r'^stock_in_request_list/$', views.redirect_stock_in_request_list, name='stock_in_request_list'),
    url(r'^get_stock_in_request_data/$', views.redirect_get_stock_in_request_data, name='get_stock_in_request_data'),
    url(r'^create_stock_in/$', views.redirect_create_stock_in, name='create_stock_in'),
    url(r'^stock_in_list/$', views.redirect_stock_in_list, name='stock_in_list'),
    url(r'^stock_in_list_data/$', views.redirect_stock_in_list_data, name='stock_in_list_data'),
    #url(r'^stock_struct_list/$', views.redirect_stock_struct_list, name='stock_struct_list'),
    #url(r'^stock_struct_list_data/$', views.redirect_stock_struct_list_data, name='stock_struct_list_data'),
    url(r'^interbranch_transfer_new/$', views.redirect_interbranch_transfer_new, name='interbranch_transfer_new'),
    url(r'^interbranch_order_save/$', views.redirect_interbranch_order_save, name='interbranch_order_save'),
    url(r'^interbranch_order_list/$', views.redirect_interbranch_order_list, name='interbranch_order_list'),
    url(r'^interbranch_order_list_data/$', views.redirect_interbranch_order_list_data, name='interbranch_order_list_data'),
    url(r'^change_interbranch_order_status/$', views.redirect_change_interbranch_order_status, name='change_interbranch_order_status'),
    url(r'^interbranch_order_print/$', views.redirect_interbranch_order_print, name='interbranch_order_print'),
    url(r'^interbranch_order_receive/$', views.redirect_interbranch_order_receive, name='interbranch_order_receive'),
    url(r'^stock_bom_order_new/$', views.redirect_stock_bom_order_new, name='stock_bom_order_new'),
    url(r'^stock_bom_order_new_data/$', views.redirect_stock_bom_order_new_data, name='stock_bom_order_new_data'),
    url(r'^stock_bom_order_save/$', views.redirect_stock_bom_order_save, name='stock_bom_order_save'),
    url(r'^stock_bom_order_update/$', views.redirect_stock_bom_order_update, name='stock_bom_order_update'),
]
