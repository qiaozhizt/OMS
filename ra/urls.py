from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^new/$', views.RaNew, name='ra_new'),
    url(r'^edit/$', views.RaEdit, name='ra_edit'),
    url(r'^list/$', views.RaList, name='ra_list'),
    url(r'^approve/$', views.ApproveList, name='ra_approve'),
    url(r'^buy_label/$', views.BuyLabel, name='ra_buy_label'),
    url(r'^stock_in/$', views.StockIn, name='ra_stock_in'),
    url(r'^inventory_status/$', views.ApproveList, name='ra_inventory_status'),

    url(r'^refund/$', views.Refund, name='ra_refund'),
    url(r'^coupon/$', views.Coupon, name='ra_coupon'),
    url(r'^close/$', views.Close, name='ra_close'),
    url(r'^cancel/$', views.Cancel, name='ra_cancel'),

    url(r'^action/$', views.Action, name='ra_action'),
]
