from django.conf.urls import url

from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    url(r'^$', views.index, name='comments_index'),

    url(r'^all/$', views.redirect_comments, name='comments'),
    url(r'^details/$', views.redirect_comments_details, name='comments_details'),
    url(r'^close/$', views.redirect_comments_close, name='comments_close'),
    url(r'^create/$',views.redirect_comments_create,name='comments_create'),
    url(r'^redirect_bizs/$', views.redirect_bizs, name='bizs'),
]

# url(r'^mgmt/$', views.index, name='mgmt'),
