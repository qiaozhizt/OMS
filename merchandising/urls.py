from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='merchandising_index'),

    # url(r'^all/$', views.redirect_comments, name='comments'),
    # url(r'^details/$', views.redirect_comments_details, name='comments_details'),
    # url(r'^close/$', views.redirect_comments_close, name='comments_close'),
    # url(r'^create/$',views.redirect_comments_create,name='comments_create'),
    # url(r'^redirect_bizs/$', views.redirect_bizs, name='bizs'),

    url(r'^category_products_index/$', views.redirect_category_products_index, name='category_products_index'),
    url(r'^category_products_index_post/$', views.redirect_category_products_index_post,
        name='category_products_index_post'),
    url(r'^refresh_product_index/$', views.redirect_refresh_product_index,
        name='refresh_product_index'),

    url(r'^products_list/$', views.redirect_products_list, name='products_list'),
    url(r'^products_list_v1/$', views.redirect_products_list_v1, name='products_list_v1'),
    url(r'^shipments_index/$', views.redirect_shipments_index, name='shipments_index'),
    url(r'^shipments_index_csv/$', views.redirect_shipments_index_csv, name='shipments_index_csv'),
    url(r'^production_operation_log_list/$', views.production_operation_log_list, name='production_operation_log_list'),
    url(r'^products_list_csv/$', views.redirect_products_list_csv, name='merchandising_products_list_csv'),
]

# url(r'^mgmt/$', views.index, name='mgmt'),
