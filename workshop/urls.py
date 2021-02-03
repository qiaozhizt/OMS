from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^assembled/$', views.redirect_assembled, name='workshop_assembled'),
    url(r'^assembling/$', views.redirect_assembling, name='workshop_assembling'),
    url(r'^glasses_return/$', views.redirect_glasses_return, name='workshop_glasses_return'),
    url(r'^redirect_construction_voucher_finished_glasses_quick/', views.redirect_construction_voucher_finished_glasses_quick, name='construction_voucher_finished_glasses_quick'),
    url(r'^lens_registration_quick/$', views.redirect_lens_registration_quick, name='workshop_lens_registration_quick'),
    url(r'^preliminary_checking_quick/$', views.redirect_preliminary_checking_quick, name='workshop_preliminary_checking_quick'),
    url(r'^distribute_lab_orders_manual_quick/$', views.redirect_distribute_lab_orders_manual_quick, name='distribute_lab_orders_manual_quick'),
    url(r'^redirect_construction_voucher_finished_glasses_quick_submit/$', views.redirect_construction_voucher_finished_glasses_quick_submit, name='workshop_construction_voucher_finished_glasses_quick_submit'),
]

# url(r'^mgmt/$', views.index, name='mgmt'),
