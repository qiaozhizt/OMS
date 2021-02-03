"""pg_oms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
import oms.views as views
from django.views.static import serve
from pg_oms import settings

urlpatterns = [
    url(r'^$', views.dashboard),
    url(r'^api/', include('api.urls')),
    url(r'^mrp/', include('mrp.urls')),

    url(r'^oms/', include('oms.urls')),
    url(r'^mgmt/', admin.site.urls),
    url(r'^report/', include('report.urls')),
    url(r'^comment/', include('comment.urls')),
    url(r'^wms/', include('wms.urls')),
    url(r'^shipment/', include('shipment.urls')),
    url(r'^qc/', include('qc.urls')),
    url(r'^purchase/', include('purchase.urls')),
    url(r'^workshop/', include('workshop.urls')),
    url(r'^merchandising/', include('merchandising.urls')),
    url(r'^vendor/', include('vendor.urls')),
    url(r'^tracking/', include('tracking.urls')),
    url(r'^ra/', include('ra.urls')),
    url(r'^media/(?P<path>.*)$', serve, {'document_root':settings.MEDIA_ROOT}),
    url(r'^accsorder/', include('accsorder.urls')),
    url(r'^stockorder/', include('stockorder.urls')),
]
