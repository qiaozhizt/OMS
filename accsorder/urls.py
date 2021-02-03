from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^accs_order_list/$', views.redirect_accs_order_list, name='accs_order_list'),
    url(r'^accs_order_list_data/$', views.redirect_accs_order_list_data, name='accs_order_list_data'),
    url(r'^change_accs_order_status/$', views.redirect_change_accs_order_status, name='change_accs_order_status'),
    url(r'^accs_order_ship/$', views.redirect_accs_order_ship, name='accs_order_ship'),
    url(r'^accs_order_action/$', views.redirect_accs_order_action, name='accs_order_action'),
    url(r'^accs_order_request_list/$', views.redirect_accs_order_request_list, name='accs_order_request_list'),
    url(r'^accs_order_request_list_data/$', views.redirect_accs_order_request_list_data, name='accs_order_request_list_data'),
    url(r'^accs_order_request_line/$', views.redirect_accs_order_request_line, name='accs_order_request_line'),
    url(r'^accs_order_request_line_data/$', views.redirect_accs_order_request_line_data, name='accs_order_request_line_data'),
    url(r'^accs_order_request_notes_print/$', views.redirect_accs_order_request_notes_print, name='accs_order_request_notes_print'),
    url(r'^accs_order_request_notes_generate_barcode/$', views.redirect_accs_order_request_notes_generate_barcode, name='accs_order_request_notes_generate_barcode'),
    url(r'^accs_order_pick_list/$', views.redirect_accs_order_pick_list, name='accs_order_pick_list'),
    url(r'^accs_order_pick_list_data/$', views.redirect_accs_order_pick_list_data, name='accs_order_pick_list_data'),
    url(r'^accs_order_pick/$', views.redirect_accs_order_pick, name='accs_order_pick'),
    url(r'^accs_to_lab/$', views.redirect_accs_to_lab, name='accs_to_lab'),
]

