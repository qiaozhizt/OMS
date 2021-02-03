from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^redirect_laborder_statistical_analysis/$', views.redirect_laborder_statistical_analysis,
        name='laborder_statistical_analysis'),
    url(r'^redirect_laborder_lens_registration_analysis/$', views.redirect_laborder_lens_registration_analysis,
        name='laborder_lens_registration_analysis'),
    # url(r'^redirect_web_order_report/$', views.redirect_web_order_report,
    #     name='web_order_report'),
    url(r'^redirect_web_order_report_v2/$', views.redirect_web_order_report_v2,
        name='web_order_report'),
    url(r'^redirect_shipping_speed_report/$', views.redirect_shipping_speed_report,
        name='shipping_speed_report'),

    url(r'^customize_report/$', views.redirect_customize_report,
        name='customize_report'),

    url(r'^customize_report_csv/$', views.redirect_customize_report_csv,
        name='customize_report_csv'),

     url(r'^customize_report_advanced/$', views.redirect_customize_report_advanced,
        name='customize_report_advanced'),

    url(r'^shipping_speed_report_new/$', views.redirect_shipping_speed_report_new,
        name='report_shipping_speed_report_new'),

    url(r'^save_shipping_speed_report_csv/$', views.redirect_save_shipping_speed_report_csv,
        name='report_save_shipping_speed_report_csv'),
    url(r'^daliy_production_report/$', views.daliy_production_report,
        name='daliy_production_report'),
    url(r'^pg_order_report/$', views.redirect_pg_order_report_csv,
        name='pg_order_report'),
    url(r'^daliy_production_return_report/$', views.daliy_production_return_report,
        name='daliy_production_return_report'),
    url(r'^pgorder_approve_processing_report/$', views.pgorder_approve_processing_report,
        name='pgorder_approve_processing_report'),
    url(r'^pgorder_approve_processing_report_generate/$', views.pgorder_approve_processing_report_generate,
        name='pgorder_approve_processing_report_generate'),
    url(r'^laborder_production_report/$', views.laborder_production_report,
        name='laborder_production_report'),
    url(r'^laborder_flow_report/$', views.laborder_flow_report,
        name='report_laborder_flow_report'),
    url(r'^laborder_flow_report_csv/$', views.laborder_flow_report_csv,
        name='report_laborder_flow_report_csv'),
    url(r'^shipment_pc_lens_lab_report/$', views.shipment_pc_lens_lab_report,
        name='report_shipment_pc_lens_lab_report'),
    url(r'^shipment_pc_lens_lab_line/$', views.shipment_pc_lens_lab_line,
        name='report_shipment_pc_lens_lab_line'),
    url(r'^pgorder_coupon_report/$', views.pgorder_coupon_report,
        name='report_pgorder_coupon_report'),
    url(r'^pgorder_coupon_report_csv/$', views.pgorder_coupon_report_csv,
        name='report_pgorder_coupon_report_csv'),
    url(r'^redirect_web_order_report_v3/$', views.redirect_web_order_report_v3,
        name='web_order_report_v3'),
    url(r'^report_purchase_order_time_report/$', views.redirect_report_purchase_order_time_report,
        name='report_purchase_order_time_report'),
    url(r'^report_purchase_order_time_report_csv/$', views.redirect_report_purchase_order_time_report_csv,
        name='report_purchase_order_time_report_csv'),

    url(r'^report_arrival_time_diff_report/$', views.redirect_arrival_time_diff_report,
        name='report_arrival_time_diff_report'),
    url(r'^report_arrival_time_diff_report_csv/$', views.redirect_arrival_time_diff_report_csv,
        name='report_arrival_time_diff_report_csv'),
    url(r'^laborder_doctor_report/$', views.laborder_doctor_report,
        name='report_laborder_doctor_report'),
    url(r'^laborder_doctor_report_csv/$', views.laborder_doctor_report_csv,
       name='report_laborder_doctor_report_csv'),
]

# url(r'^mgmt/$', views.index, name='mgmt'),
