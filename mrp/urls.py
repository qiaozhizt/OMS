from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='mrp_index'),
    url(r'^tasks/$', views.redirect_tasks, name='tasks'),

]

# url(r'^mgmt/$', views.index, name='mgmt'),
