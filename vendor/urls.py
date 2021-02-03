from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='vendor_index'),
    url(r'^lens/$', views.redirect_lens, name='lens'),
    url(r'^lens_by_lbo/$', views.redirect_lens_by_lbo, name='lens_by_lbo'),
    url(r'^lens_by_vd/$', views.redirect_lens_by_vd, name='lens_by_vd'),

    url(r'^lens_orders/$', views.redirect_lens_orders, name='lens_orders'),
    url(r'^lens_order/new/$', views.redirect_lens_order_new, name='lens_order_new'),

    url(r'^distribute_lab_orders/$', views.redirect_distribute_lab_orders, name='distribute_lab_orders'),
    url(r'^distribute_lab_orders_manual/$', views.redirect_distribute_lab_orders_manual,
        name='distribute_lab_orders_manual'),
    url(r'^set_wc_lens_from_json/$', views.set_wc_lens_from_json, name='set_wc_lens_from_json'),
]

# url(r'^mgmt/$', views.index, name='mgmt'),
