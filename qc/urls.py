from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='index'),

    url(r'^all/$', views.index, name='qc'),
    url(r'^qc_glasses_final_inspection_technique/$', views.redirect_qc_glasses_final_inspection_technique,
        name='qc_glasses_final_inspection_technique'),

    url(r'^qc_glasses_final_inspection_technique_create/$', views.redirect_qc_glasses_final_inspection_technique_create,
        name='qc_glasses_final_inspection_technique_create'),
    url(r'^qc_glasses_final_inspection_technique_list/$', views.qc_glasses_final_inspection_technique_list,
        name='qc_glasses_final_inspection_technique_list'),

    url(r'^qc_glasses_final_inspection_visual_create/$', views.redirect_qc_glasses_final_inspection_visual_create,
        name='qc_glasses_final_inspection_visual_create'),

    url(r'^lens_registration/$', views.redirect_lens_registration,
        name='lens_registration'),

    url(r'^preliminary_checking/$', views.redirect_preliminary_checking,
        name='preliminary_checking'),

    url(r'^received_lens/$', views.redirect_received_lens,
        name='received_lens'),

    url(r'^glasses_return/$', views.redirect_glasses_return,
        name='glasses_return'),

    url(r'^glasses_return_print/$', views.redirect_glasses_return_print,
        name='glasses_return_print'),

    url(r'^quality_inspection_report/$',views.redirect_quality_inspection_report,
        name='quality_inspection_report'),

    url(r'^glasses_return_list/$', views.redirect_glasses_return_list,
        name='glasses_return_list'),

    url(r'^glasses_return_detail/$', views.redirect_glasses_return_detail,
        name='glasses_return_detail'),

    url(r'^frame_delivery_submit/$', views.redirect_frame_delivery_submit,
        name='qc_frame_delivery_submit'),
    url(r'^get_lens_cyl/$', views.redirect_get_lens_cyl,
        name='qc_get_lens_cyl'),
    url(r'^get_lens_sph/$', views.redirect_get_lens_sph,
        name='qc_get_lens_sph'),
    url(r'^lens_delivery_submit/$', views.redirect_lens_delivery_submit,
        name='qc_lens_delivery_submit'),
    url(r'^lens_return_list/$', views.redirect_lens_return_list,
        name='lens_return_list'),
    url(r'^lens_return_list_csv/$', views.redirect_lens_return_list_csv,
        name='lens_return_list_csv'),
]
